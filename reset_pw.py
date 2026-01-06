from database import get_db
from sqlalchemy import text
import bcrypt

db = next(get_db())
new_pw = bcrypt.hashpw(b'Doil@gi2307', bcrypt.gensalt()).decode()
db.execute(text("UPDATE admin_users SET password_hash = :hash WHERE username = 'admin'"), {"hash": new_pw})
db.commit()
print("Admin password reset to: Doil@gi2307")
