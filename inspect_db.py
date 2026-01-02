import os
from sqlalchemy import create_engine, text

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("Error: DATABASE_URL not set")
    exit(1)

engine = create_engine(db_url)

print("Inspecting tiers table:")
with engine.connect() as conn:
    # Postgres specific query to get columns
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'products'"))
    for row in result:
        print(row[0])
