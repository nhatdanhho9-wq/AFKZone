"""
AFKZone Remote Backend v2 - Clean Implementation
Based on API Spec JSON
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import init_db
from app.routers import auth, user, devices, trusted, remote, plans, notifications, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    init_db()
    print("BACKEND_V2_STARTUP port=21121")
    yield
    print("BACKEND_V2_SHUTDOWN")


app = FastAPI(
    title="AFKZone Remote API",
    description="Backend for AFKZone Remote Control App",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS for mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"ok": False, "error_code": "INTERNAL_ERROR", "message": str(exc)}
    )


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(devices.router, tags=["devices"])
app.include_router(trusted.router, prefix="/trusted", tags=["trusted"])
app.include_router(remote.router, prefix="/remote", tags=["remote"])
app.include_router(plans.router, tags=["plans"])
app.include_router(notifications.router, prefix="/user", tags=["notifications"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


@app.get("/health")
async def health():
    return {"ok": True, "status": "healthy", "version": "2.0.0"}
