"""
AFKZone Backend - Clean-Room Implementation
Main FastAPI application entry point.
"""
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.routers import auth, devices, remote, trusted, sessions


# Database setup
DB_PATH = Path(__file__).parent.parent / "data" / "afkzone.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_db():
    """Initialize database with schema."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Account table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS account (
            account_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Device table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS device (
            device_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            device_name TEXT NOT NULL,
            device_type TEXT DEFAULT 'android',
            online INTEGER DEFAULT 0,
            last_seen TEXT,
            unattended_mode TEXT DEFAULT 'disabled',
            remote_password_hash TEXT,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_device_account ON device(account_id)")
    
    # Remote request table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS remote_request (
            request_id TEXT PRIMARY KEY,
            target_device_id TEXT NOT NULL,
            requester_account_id TEXT,
            requester_device_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            expires_at TEXT,
            session_id TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_request_target ON remote_request(target_device_id)")
    
    # Trusted allowlist table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trusted_allowlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_account_id TEXT NOT NULL,
            target_device_id TEXT NOT NULL,
            requester_account_id TEXT,
            requester_device_id TEXT,
            status TEXT DEFAULT 'pending',
            allow_input_control INTEGER DEFAULT 1,
            allow_file_transfer INTEGER DEFAULT 0,
            created_at TEXT,
            approved_at TEXT,
            expires_at TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_trusted_owner ON trusted_allowlist(owner_account_id)")
    
    # Share token table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS share_token (
            token TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            account_id TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            max_uses INTEGER DEFAULT 1,
            uses_count INTEGER DEFAULT 0,
            revoked INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"DATABASE_INIT path={DB_PATH}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    init_db()
    print("BACKEND_STARTUP port=21121")
    yield
    print("BACKEND_SHUTDOWN")


# Create FastAPI app
app = FastAPI(
    title="AFKZone API",
    description="Clean-Room Remote Control Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "ok": False,
            "error_code": "VALIDATION_ERROR",
            "message": str(exc.errors()[0]["msg"]) if exc.errors() else "Validation error"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error_code": "INTERNAL_ERROR",
            "message": str(exc)
        }
    )


# Include routers
app.include_router(auth.router, prefix="", tags=["auth"])
app.include_router(devices.router, prefix="", tags=["devices"])
app.include_router(remote.router, prefix="", tags=["remote"])
app.include_router(trusted.router, prefix="", tags=["trusted"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"ok": True, "status": "healthy"}
