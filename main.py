# main.py
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, cast
from crud import create_order, get_orders
from notifications.sms_utils import send_sms
from notifications.email_utils import insert_order_to_supabase, send_order_email
from ultramsg.ultramsg_utils import send_order_whatsapp
from schemas import OrderOut, OrderCreated
from notifications.notification_routes import router as notification_router
import logging
from sqlalchemy.exc import SQLAlchemyError
import os
import requests
from dotenv import load_dotenv

# -----------------------------
# App setup
# -----------------------------
app = FastAPI(
    title="Restaurant Backend API",
    description="FastAPI backend for restaurant order management with notifications",
    version="1.0.0"
)

# Load environment variables
load_dotenv()

# -----------------------------
# CORS setup
# -----------------------------
raw_allowed = os.getenv("BACKEND_ALLOW_ORIGINS", "*")
allowed_origins = ["*"] if raw_allowed.strip() == "*" else [o.strip() for o in raw_allowed.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Include notification routes
# -----------------------------
app.include_router(notification_router)

logger = logging.getLogger("uvicorn.error")

# -----------------------------
# Default favicon
# -----------------------------
DEFAULT_FAVICON = b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <rect width="16" height="16" fill="#4f46e5"/>
  <text x="8" y="12" font-size="10" text-anchor="middle" fill="white">R</text>
</svg>
"""

@app.get("/favicon.ico")
async def favicon():
    return Response(content=DEFAULT_FAVICON, media_type="image/svg+xml")

# -----------------------------
# Schemas
# -----------------------------
class OrderIn(BaseModel):
    name: str
    item: str
    phone: str

# -----------------------------
# Routes
# -----------------------------
@app.post("/order", response_model=OrderCreated, status_code=201)
def post_order(payload: OrderIn) -> Dict[str, Any]:
    try:
        order = create_order(payload.name, payload.item, payload.phone)
    except RuntimeError as exc:
        logger.exception("Failed to create order")
        raise HTTPException(status_code=500, detail=str(exc))

    owner_phone = os.getenv("ADMIN_PHONE_NUMBER")
    if owner_phone:
        try:
            send_sms(owner_phone, f"New order: {order.item} from {order.name}")
        except Exception:
            logger.exception("Failed to send SMS for order %s", getattr(order, "id", "?"))

    whatsapp_sent = False
    try:
        supa_result = insert_order_to_supabase(order)
        if supa_result.get("success"):
            try:
                send_order_email(supa_result.get("row", {}))
            except Exception:
                logger.exception("Failed to send email for order %s", getattr(order, "id", "?"))

            try:
                whatsapp_result = send_order_whatsapp(order)
                if whatsapp_result.get("success"):
                    whatsapp_sent = True
                    logger.info("WhatsApp sent successfully for order %s", getattr(order, "id", "?"))
                else:
                    logger.warning("WhatsApp failed for order %s: %s", getattr(order, "id", "?"), whatsapp_result.get("error"))
            except Exception:
                logger.exception("Error sending WhatsApp for order %s", getattr(order, "id", "?"))
        else:
            logger.warning("Supabase insert failed for order %s: %s", getattr(order, "id", "?"), supa_result.get("error"))
            try:
                whatsapp_result = send_order_whatsapp(order)
                if whatsapp_result.get("success"):
                    whatsapp_sent = True
                    logger.info("WhatsApp sent but Supabase failed for order %s", getattr(order, "id", "?"))
            except Exception:
                logger.exception("Failed WhatsApp when Supabase failed for order %s", getattr(order, "id", "?"))
    except Exception:
        logger.exception("Error saving to Supabase or sending notification for order %s", getattr(order, "id", "?"))

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

# -----------------------------
# OpenCage geocoding
# -----------------------------
OPENCAGE_KEY = os.getenv("OPENCAGE_KEY")

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
    return {"address": results[0].get("formatted")}

# -----------------------------
# Exception handlers
# -----------------------------
@app.exception_handler(SQLAlchemyError)
def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Database error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "database error"})

@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "internal server error"})

# -----------------------------
# Startup logging
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"✅ FastAPI starting on PORT: {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
