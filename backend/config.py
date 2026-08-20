import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory (HealthAI root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    """Application configuration loaded dynamically from environment variables."""

    @property
    def GEMINI_API_KEY(self) -> str:
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        return os.getenv("GEMINI_API_KEY", "").strip()

    @property
    def GEMINI_MODEL(self) -> str:
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        return os.getenv("GEMINI_MODEL", "gemini-3.7-flash").strip()

    @property
    def HOST(self) -> str:
        return os.getenv("HOST", "127.0.0.1").strip()

    @property
    def PORT(self) -> int:
        try:
            return int(os.getenv("PORT", "8000").strip())
        except ValueError:
            return 8000

    def is_gemini_configured(self) -> bool:
        """Check whether a valid Gemini API key is configured."""
        key = self.GEMINI_API_KEY
        return bool(key and key != "your_gemini_api_key_here")


settings = Settings()
