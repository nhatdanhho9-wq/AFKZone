"""
Database setup and connection.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "afkzone_v2.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_db()
    cur = conn.cursor()
    
    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            avatar_url TEXT,
            plan TEXT DEFAULT 'free',
            plan_expires_at TEXT,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    
    # Refresh tokens table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            revoked INTEGER DEFAULT 0
        )
    """)
    
    # Devices table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            owner_user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT DEFAULT 'cloud',
            status TEXT DEFAULT 'offline',
            vcpu INTEGER DEFAULT 2,
            ram_gb INTEGER DEFAULT 4,
            description TEXT,
            remote_password_hash TEXT,
            last_seen_at TEXT,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_devices_owner ON devices(owner_user_id)")
    
    # Trusted devices table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trusted_devices (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, device_id)
        )
    """)
    
    # Sessions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            host_device_id TEXT NOT NULL,
            client_user_id TEXT NOT NULL,
            state TEXT DEFAULT 'requested',
            created_at TEXT NOT NULL,
            connected_at TEXT,
            disconnected_at TEXT,
            last_stats_at TEXT
        )
    """)
    
    # Plans table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            price_usd REAL NOT NULL,
            billing_period TEXT DEFAULT 'month',
            vcpu INTEGER,
            ram_gb INTEGER,
            features TEXT
        )
    """)
    
    # Notifications table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT,
            data TEXT,
            read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    
    # Seed default plans
    cur.execute("SELECT COUNT(*) FROM plans")
    if cur.fetchone()[0] == 0:
        plans = [
            ("plan_starter", "STARTER_UNIT", "Starter Unit", 5, "month", 2, 4, "[]"),
            ("plan_pro", "PRO_GLADIATOR", "Pro Gladiator", 15, "month", 8, 16, '["Priority Support"]'),
            ("plan_team", "TEAM_SERVER", "Team Server", 30, "month", 8, 32, '["Dedicated Network"]'),
        ]
        cur.executemany(
            "INSERT INTO plans (id, code, name, price_usd, billing_period, vcpu, ram_gb, features) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            plans
        )
    
    conn.commit()
    conn.close()
    print(f"DATABASE_INIT path={DB_PATH}")
