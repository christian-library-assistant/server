import os
from dotenv import load_dotenv

ENV_LOADED = False

def get_env(key: str):
    global ENV_LOADED
    if not ENV_LOADED:
        load_dotenv()
        ENV_LOADED = True
    return os.getenv(key)

ANTHROPIC_API_KEY = get_env("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = get_env("GOOGLE_API_KEY")
MANTICORE_API_URL = get_env("MANTICORE_API_URL")