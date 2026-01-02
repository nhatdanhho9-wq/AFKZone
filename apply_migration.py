import os
from sqlalchemy import create_engine, text

# Get DB URL from env
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("Error: DATABASE_URL not set")
    exit(1)

engine = create_engine(db_url)

# Read migration file
with open('/tmp/20260102_notifications_api.sql', 'r') as f:
    sql = f.read()

print("Applying migration...")
with engine.connect() as conn:
    # Split by semicolon to run statements individually if needed, 
    # but sqlalchemy can handle blocks usually. Let's try executing as block first.
    # Postgres usually handles multiple statements in one go.
    conn.execute(text(sql))
    conn.commit()

print("Migration applied successfully!")
