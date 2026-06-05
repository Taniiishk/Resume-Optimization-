from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "openrouter"
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-oss-120b:free"

    # Legacy Google Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    host: str = "0.0.0.0"
    port: int = 8001

    @property
    def api_key(self) -> str:
        if self.llm_provider == "openrouter":
            return self.openrouter_api_key
        return self.gemini_api_key

    @property
    def model_name(self) -> str:
        if self.llm_provider == "openrouter":
            return self.openrouter_model
        return self.gemini_model


settings = Settings()
