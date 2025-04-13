import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(dotenv_path=BASE_DIR / ".env")

DB_NAME = os.path.join(BASE_DIR.parent, os.getenv("DB_NAME"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
