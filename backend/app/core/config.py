from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "HAL 2.0"
    api_prefix: str = "/api/v1"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-6"
    openai_api_key: str | None = None
    openai_transcribe_model: str = "gpt-4o-mini-transcribe"
    max_audio_upload_mb: int = 20

    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    elevenlabs_voice_id_el: str | None = None
    elevenlabs_voice_id_en: str | None = None

    provider_refresh_hours: int = 24

    database_url: str | None = None
    jwt_secret: str | None = None
    admin_password: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
