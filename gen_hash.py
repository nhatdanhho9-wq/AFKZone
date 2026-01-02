#!/usr/bin/env python3
import bcrypt
password = b'afk_4nA3UWW1XUFKlqPOvnVR6Q'
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(hashed.decode())
