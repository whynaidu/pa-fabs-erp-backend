from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.models import *
from backend.api import auth, pos, inward, outward, returns, looms, manufacturing, deliveries, admin, beams, inventory

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
