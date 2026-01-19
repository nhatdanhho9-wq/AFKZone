"""
Configuration settings.
"""
import os

# JWT Settings
JWT_SECRET = os.getenv("JWT_SECRET", "afkzone-v2-secret-key-2026")
ACCESS_TOKEN_TTL = 86400  # 24 hours
REFRESH_TOKEN_TTL = 86400 * 30  # 30 days

# TURN Settings
TURN_SECRET = os.getenv("AFK_TURN_SECRET", "afkzone-turn-secret")
TURN_HOST = os.getenv("AFK_TURN_HOST", "turn.afkzone.cloud")
TURN_TTL = 86400

# Rate Limiting
RATE_LIMIT_DEFAULT = 100  # requests per minute
