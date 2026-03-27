import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "7315557969:AAEGhVzqH2CAVpTlmOZwVUtredd6tPjQtXY")
ADMIN_IDS: list[int] = list(map(int, os.getenv("ADMIN_IDS", "0").split(",")))
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "shopbot.db")
ITEMS_PER_PAGE: int = 5
