import os
from pathlib import Path

# Base project path (one level above src)
BASE_DIR = Path(__file__).resolve().parent.parent

# Storage configuration
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", BASE_DIR / "dist"))
SOURCES_DIR = Path(os.getenv("SOURCES_DIR", BASE_DIR / "sources"))

# Database path
SQLITE_DB_PATH = Path(os.getenv("SQLITE_DB_PATH", DATA_DIR / "data.db"))

# Server settings - Port 8001 to coexist with metrics-collector-retriever (8000) and cms-core-api (8080)
PORT = int(os.getenv("PORT", 8001))
HOST = os.getenv("HOST", "0.0.0.0")

# Ensure required directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
SOURCES_DIR.mkdir(parents=True, exist_ok=True)
