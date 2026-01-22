import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
MODE = os.getenv("MODE", "dev")  # dev / prod