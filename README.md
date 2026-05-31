# PA FABS ERP — Backend

FastAPI + SQLAlchemy backend for the PA FABS Textile ERP. Deployed on Render with managed Postgres.

## Stack
- FastAPI (`backend/main.py`), routers under `/api/*`
- SQLAlchemy models, Postgres in prod / SQLite locally
- JWT auth (Bearer tokens)

## Run locally
```bash
pip install -r requirements.txt
cp .env.example .env          # defaults to SQLite; set SECRET_KEY
uvicorn backend.main:app --reload --port 3001
```
Tables are created and admin/user/looms are seeded automatically on startup.

Default logins: `admin`/`admin123`, `user`/`user123`.

## Deploy (Render)
`render.yaml` is a Blueprint that provisions a free web service + free Postgres.
Render injects `DATABASE_URL`; `SECRET_KEY` is auto-generated; set `ALLOWED_ORIGINS`
to the deployed frontend URL.

- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Health check: `GET /health`

## Env vars
| Var | Purpose |
|-----|---------|
| `DATABASE_URL` | Postgres connection (Render-injected). Falls back to SQLite if unset. |
| `SECRET_KEY` | JWT signing key. Required in prod. |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins (the frontend URL). |
