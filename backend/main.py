from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.models import *
from backend.api import auth, pos, inward, outward, returns, looms, manufacturing, deliveries, admin, beams, inventory, dashboard, export

app = FastAPI(
    title="PA FABS Textile ERP API",
    description="Full-stack Textile ERP System for PA FABS",
    version="2.0.0"
)

# CORS locked to the configured origins (the deployed frontend URL). The app
# authenticates with Bearer tokens, not cookies, so credentials are off — which
# also lets us use explicit origins cleanly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_AUDIT_ACTION = {"POST": "create", "PUT": "update", "PATCH": "update", "DELETE": "delete"}
_AUDIT_SPECIAL = {"login": "login", "register": "register", "forgot-password": "reset-password"}


def _record_audit(request, method, path, status):
    from backend.database import SessionLocal
    from backend.models.audit import AuditLog
    from backend.services.auth_service import decode_access_token
    import uuid
    username = None
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        payload = decode_access_token(auth.split(" ", 1)[1])
        if payload:
            username = payload.get("sub")
    parts = [p for p in path.replace("/api/", "", 1).split("/") if p]
    entity = parts[0] if parts else None
    entity_id = parts[1] if len(parts) > 1 else None
    action = _AUDIT_SPECIAL.get(entity, _AUDIT_ACTION.get(method))
    db = SessionLocal()
    try:
        db.add(AuditLog(id=f"audit_{uuid.uuid4().hex}", username=username, action=action,
                        entity=entity, entity_id=entity_id, method=method, path=path,
                        status_code=status))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@app.middleware("http")
async def audit_middleware(request, call_next):
    response = await call_next(request)
    try:
        if request.method in _AUDIT_ACTION and request.url.path.startswith("/api/"):
            _record_audit(request, request.method, request.url.path, response.status_code)
    except Exception:
        pass
    return response


app.include_router(auth.router, prefix="/api")
app.include_router(pos.router, prefix="/api")
app.include_router(inward.router, prefix="/api")
app.include_router(outward.router, prefix="/api")
app.include_router(returns.router, prefix="/api")
app.include_router(looms.router, prefix="/api")
app.include_router(manufacturing.router, prefix="/api")
app.include_router(deliveries.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(beams.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(export.router, prefix="/api")


@app.on_event("startup")
def on_startup():
    # Create tables + seed defaults on a fresh database (idempotent).
    from backend.bootstrap import init_and_seed
    init_and_seed()


@app.get("/")
def root():
    return {
        "message": "PA FABS Textile ERP API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
