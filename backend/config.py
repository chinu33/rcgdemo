import os
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SEED_DIR = DATA_DIR / "seed"
DB_PATH = DATA_DIR / "rcg.db"
FRONTEND_DIR = ROOT_DIR / "frontend"

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    pass


@dataclass
class Settings:
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3-pro")
    input_cost_per_1m: float = float(os.getenv("GEMINI_INPUT_COST_PER_1M", "1.25"))
    output_cost_per_1m: float = float(os.getenv("GEMINI_OUTPUT_COST_PER_1M", "10.00"))

    langsmith_tracing: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY", "")
    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "rcg-command-center")
    langsmith_endpoint: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    demo_mode_fallback: bool = os.getenv("DEMO_MODE_FALLBACK", "true").lower() == "true"

    @property
    def has_llm(self) -> bool:
        return bool(self.google_api_key) and self.google_api_key != "your-google-api-key-here"

    @property
    def is_demo_mode(self) -> bool:
        return not self.has_llm and self.demo_mode_fallback


settings = Settings()


def _langsmith_enabled() -> bool:
    key = settings.langsmith_api_key
    return (
        settings.langsmith_tracing
        and bool(key)
        and key != "your-langsmith-api-key-here"
    )


if _langsmith_enabled():
    # Set BOTH env-var name variants — langsmith/langchain switched naming and
    # different versions of the SDK look at different keys.
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
    print(f"[rcg] LangSmith tracing ENABLED · project='{settings.langsmith_project}'")
else:
    print("[rcg] LangSmith tracing DISABLED (set LANGSMITH_TRACING=true and a real LANGSMITH_API_KEY in .env)")


# Re-export for callers that want to read the live state
settings.langsmith_active = _langsmith_enabled()
