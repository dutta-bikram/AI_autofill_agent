import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # Browser Automation Settings
    HEADLESS_BROWSER: bool = os.getenv("HEADLESS_BROWSER", "false").lower() in ("true", "1", "yes")
    BROWSER_SLOW_MO: int = int(os.getenv("BROWSER_SLOW_MO", "50"))
    HIGHLIGHT_ELEMENTS: bool = os.getenv("HIGHLIGHT_ELEMENTS", "true").lower() in ("true", "1", "yes")

    # Human-In-The-Loop (HITL) Mode
    # "always": ask for review before filling
    # "low_confidence": only prompt if confidence < threshold
    # "never": full autonomous fill
    HITL_MODE: str = os.getenv("HITL_MODE", "always").lower()
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))

    # Storage & Persistence Paths
    DATA_DIR: Path = BASE_DIR / "data"
    CHROMA_PERSIST_DIR: Path = BASE_DIR / "data" / "chroma_db"
    USER_PROFILE_PATH: Path = BASE_DIR / "data" / "user_profile.json"
    DOCUMENTS_DIR: Path = BASE_DIR / "data" / "documents"

    # Server Settings
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    SERVER_HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")

    def ensure_directories(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        self.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
