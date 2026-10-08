import os
BASE = os.path.abspath(os.path.dirname(__file__))
class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///" + os.path.join(BASE, "potholeiq.db"))
    UPLOAD_DIR = os.path.join(BASE, "uploads")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    AUTHORITY_PIN = os.getenv("AUTHORITY_PIN", "2026")
    DUPLICATE_RADIUS_M = 25
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
    RAIN_DEMO = os.getenv("RAIN_DEMO", "0") == "1"   # skip network, use synthetic rainfall
    RAIN_CACHE_SECONDS = 1800
    DEFAULT_CENTER = (11.4102, 77.6980)  # Erode
    ALLOWED_EXT = {"jpg", "jpeg", "png", "webp"}
