# restaurant-backend

This repository is a small FastAPI backend for a restaurant ordering demo. It uses SQLAlchemy ORM for models and can connect to either a local SQLite database for development or a Postgres database hosted on Supabase for production.

## Quick status
- The code now requires a real `DATABASE_URL` when you intend to use Supabase.
- For local development you can temporarily set a direct SQLite URL in `.env` (instructions below) or use the Supabase DB details.

## Required environment
Create a `.env` file in the project root with a `DATABASE_URL` value.

Examples:

- Supabase (direct DB connection) — recommended for production/staging

  Replace <PASSWORD> and <your-host> with values from your Supabase Project > Settings > Database > Connection string (direct DB URI):

  ```text
  DATABASE_URL=postgresql+psycopg2://postgres:<PASSWORD>@db.<your-host>.supabase.co:5432/postgres
  ```

  Notes:
  - Use the direct DB connection string that includes `postgresql+psycopg2://` to ensure SQLAlchemy uses the psycopg2 driver.
  - Keep these credentials secret — don't commit `.env` to source control.

- Local SQLite (development quick-start)

  If you want to run locally without Supabase, set:

  ```text
  DATABASE_URL=sqlite:///./dev.db
  ```

  This creates `dev.db` in the project root when you run `create_tables.py`.

## Setup
1. (Optional) Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies (you can use `pip`):

```powershell
pip install -r requirements.txt
# or install directly
pip install fastapi sqlalchemy python-dotenv uvicorn psycopg2-binary
```

3. Set `DATABASE_URL` in `.env` (see examples above).

4. Create tables (runs `Base.metadata.create_all` on the configured database):

```powershell
python create_tables.py
```

This will print `Tables created` on success.

## Run the server
Start the FastAPI app with uvicorn:

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

If you use Supabase, ensure the `DATABASE_URL` points to your Supabase DB before running.

## Test the API
- POST an order:

```powershell
curl -X POST "http://127.0.0.1:8000/order" -H "Content-Type: application/json" -d '{ "name":"Alice", "item":"Pizza", "phone":"+1234567890" }'
```

- GET orders:

```powershell
curl "http://127.0.0.1:8000/orders"
```

## Troubleshooting
- If you see an error about `DATABASE_URL` being a placeholder (contains `<your-host>`), replace the placeholder with the real host value from Supabase.
- If you get connection errors to Supabase, ensure your network allows outbound connections to the Supabase host and that your password is correct.

## Supabase production checklist (short)

- Use the Supabase *direct DB* connection string (service_role key is for server only). Put it into `.env` as `DATABASE_URL`.
- Consider using a dedicated server role or user with limited permissions for backend.
- Use RLS (Row Level Security) on the `orders` table in Supabase. Example SQL to run in Supabase SQL editor:

```sql
-- enable RLS
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;

-- allow inserts from the server (service_role) - this policy example assumes server uses the supabase service role
CREATE POLICY server_insert ON public.orders
  FOR INSERT USING (true);

-- read policy for authenticated users (example)
CREATE POLICY select_authenticated ON public.orders
  FOR SELECT USING (auth.role() = 'authenticated');
```

Note: RLS policies depend on how your frontend authenticates. For server-side inserts use your Supabase service_role key (keep it secret). For frontend direct DB access you must design policies carefully.

## Insert sample data (Supabase)
If you have `DATABASE_URL` set to your Supabase DB, run:

```powershell
python create_tables.py
python sample_data.py
```

This will create tables (if missing) and insert sample orders.

## Next steps I can help with
- Add tests (pytest) and CI.
- Add a `.env.example` and `.gitignore` entries.
- Add a small admin endpoint or web UI.

If you want me to continue, say which task from the todo list you want me to run next (1–4).