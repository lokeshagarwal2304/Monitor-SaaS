import os
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-please-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

DATABASE_DIR = BASE_DIR / "data"
DATABASE_PATH = DATABASE_DIR / "monitoring.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

DEFAULT_CHECK_INTERVAL = 5
REQUEST_TIMEOUT = 10

ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]