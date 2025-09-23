import os
import logging
from dotenv import load_dotenv

ENV_LOADED = False


def get_env(key: str):
    global ENV_LOADED
    if not ENV_LOADED:
        load_dotenv()
        ENV_LOADED = True
    return os.getenv(key)


# Environment and API settings
ENVIRONMENT = get_env("ENVIRONMENT") or "production"
ANTHROPIC_API_KEY = get_env("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = get_env("GOOGLE_API_KEY")
MANTICORE_API_URL = get_env("MANTICORE_API_URL")

# Development environment check
IS_DEVELOPMENT = ENVIRONMENT.lower() in ["development", "dev", "developer"]

# Configure logging based on environment
def configure_logging():
    """Configure logging based on environment."""
    if IS_DEVELOPMENT:
        # Verbose logging for development
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        # Minimal logging for production
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

# Configure logging on import
configure_logging()