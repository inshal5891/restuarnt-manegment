# main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, cast
from crud import create_order, get_orders
from notifications.sms_utils import send_sms
# Supabase + email helpers for order notifications
from notifications.email_utils import insert_order_to_supabase, send_order_email
# UltraMsg WhatsApp integration
from ultramsg.ultramsg_utils import send_order_whatsapp
from schemas import OrderOut, OrderCreated
from notifications.notification_routes import router as notification_router
import logging
from sqlalchemy.exc import SQLAlchemyError
import os
import requests
from dotenv import load_dotenv


app = FastAPI(
    title="Restaurant Backend API",
    description="FastAPI backend for restaurant order management with notifications",
    version="1.0.0"
)

# Load environment variables from .env (if present) as early as possible so
# module-level config values read the correct environment.
load_dotenv()

# Configure CORS origins from environment variable for flexibility in different
# environments. Set `BACKEND_ALLOW_ORIGINS` to a comma-separated list of origins
# (e.g. "http://localhost:3000,https://example.com"). If not set, default to
# the local Next.js dev URL.
raw_allowed = os.getenv("BACKEND_ALLOW_ORIGINS", "http://localhost:3000")
if raw_allowed.strip() == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [o.strip() for o in raw_allowed.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include notification routes
app.include_router(notification_router)

logger = logging.getLogger("uvicorn.error")


class OrderIn(BaseModel):
    name: str
    item: str
    phone: str


@app.post("/order", response_model=OrderCreated, status_code=201)
def post_order(payload: OrderIn) -> Dict[str, Any]:
    try:
        order = create_order(payload.name, payload.item, payload.phone)
    except RuntimeError as exc:
        logger.exception("Failed to create order")
        raise HTTPException(status_code=500, detail=str(exc))

    # Send SMS to owner or customer (non-blocking in production)
    try:
        send_sms("+92300xxxxxxx", f"New order: {order.item} from {order.name}")
    except Exception:
        # Log SMS delivery failure but do not fail the request
        logger.exception("Failed to send SMS for order %s", getattr(order, "id", "?"))

    # Persist the order into Supabase `orders` table (best-effort). If Supabase
    # save succeeds we also send an email notification and WhatsApp via UltraMsg.
    whatsapp_sent = False
    
    try:
        supa_result = insert_order_to_supabase(order)
        if supa_result.get("success"):
            # Supabase insert succeeded - proceed with notifications
            # Use the returned row representation to build the email
            try:
                send_order_email(supa_result.get("row", {}))
            except Exception:
                logger.exception("Failed to send email notification for order %s", getattr(order, "id", "?"))

            # Send WhatsApp notification via UltraMsg after successful Supabase insert
            try:
                whatsapp_result = send_order_whatsapp(order)
                if whatsapp_result.get("success"):
                    whatsapp_sent = True
                    logger.info("WhatsApp notification sent successfully for order %s", getattr(order, "id", "?"))
                else:
                    logger.warning("WhatsApp notification failed for order %s: %s", getattr(order, "id", "?"), whatsapp_result.get("error"))
            except Exception:
                logger.exception("Unexpected error sending WhatsApp for order %s", getattr(order, "id", "?"))
        else:
            # Supabase insert failed - still attempt to send WhatsApp as best-effort
            logger.warning("Supabase insert failed for order %s: %s", getattr(order, "id", "?"), supa_result.get("error"))
            try:
                whatsapp_result = send_order_whatsapp(order)
                if whatsapp_result.get("success"):
                    # WhatsApp sent even though Supabase failed
                    whatsapp_sent = True
                    logger.info("WhatsApp sent but Supabase failed for order %s", getattr(order, "id", "?"))
            except Exception:
                logger.exception("Failed to send WhatsApp when Supabase also failed for order %s", getattr(order, "id", "?"))
    except Exception:
        logger.exception("Unexpected error while saving to Supabase or sending notification for order %s", getattr(order, "id", "?"))

    # Build response: include notification status if WhatsApp was sent
    response: Dict[str, Any] = {"id": order.id, "status": "created"}
    if whatsapp_sent:
        response["notification"] = "success"
    
    return response


@app.get("/orders", response_model=List[OrderOut])
def list_orders() -> List[OrderOut]:
    try:
        orders = get_orders()
    except RuntimeError as exc:
        logger.exception("Failed to fetch orders")
        raise HTTPException(status_code=500, detail=str(exc))

    return cast(List[OrderOut], orders)


# OpenCage geocoding endpoint (returns formatted address for lat/lng)
OPENCAGE_KEY = os.getenv("OPENCAGE_KEY", "YOUR_OPENCAGE_API_KEY")


@app.get("/get-address")
def get_address(lat: float, lng: float):
    if not OPENCAGE_KEY or OPENCAGE_KEY == "YOUR_OPENCAGE_API_KEY":
        raise HTTPException(status_code=500, detail="OpenCage API key not configured")

    url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lng}&key={OPENCAGE_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.exception("OpenCage request failed: %s", exc)
        raise HTTPException(status_code=502, detail="failed to fetch address")

    results = cast(List[Dict[str, Any]], data.get("results") or [])
    if not results:
        raise HTTPException(status_code=404, detail="address not found")
    first: Dict[str, Any] = results[0]
    address = first.get("formatted")
    return {"address": address}


@app.exception_handler(SQLAlchemyError)
def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Database error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "database error"})


@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "internal server error"})
