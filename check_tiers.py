import os
from sqlalchemy import create_engine, text

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("Error: DATABASE_URL not set")
    exit(1)

engine = create_engine(db_url)

print("Checking tier_key values:")
with engine.connect() as conn:
    result = conn.execute(text("SELECT tier_key FROM tiers"))
    for row in result:
        print(row[0])
