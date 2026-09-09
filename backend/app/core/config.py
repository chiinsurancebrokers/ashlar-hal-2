from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "HAL 2.0"
    api_prefix: str = "/api/v1"

    # OpenAI powers HAL's conversational adviser and speech transcription.
    openai_api_key: str | None = None
    openai_chat_model: str = "gpt-5.6-terra"
    openai_chat_max_output_tokens: int = 1400
    openai_chat_timeout_seconds: int = 60
    openai_transcribe_model: str = "gpt-4o-mini-transcribe"

    # Legacy variables are accepted so older Railway environments keep loading.
    # HAL v8.4 does not call Anthropic.
    anthropic_api_key: str | None = None
    anthropic_model: str | None = None
    max_audio_upload_mb: int = 20

    elevenlabs_api_key: str | None = None
    # HAL's primary male multilingual adviser voice.
    # Default: ElevenLabs Adam. Override in Railway without code changes.
    hal_male_voice_id: str = "pNInz6obpgDQGcFmaJgB"
    elevenlabs_voice_id: str | None = None
    elevenlabs_voice_id_el: str | None = None
    elevenlabs_voice_id_en: str | None = None

    provider_refresh_hours: int = 24

    database_url: str | None = None
    jwt_secret: str | None = None
    admin_password: str | None = None

    # Gmail API lead delivery (OAuth 2.0)
    gmail_client_id: str | None = None
    gmail_client_secret: str | None = None
    gmail_refresh_token: str | None = None
    gmail_sender_email: str | None = None
    gmail_lead_recipient: str | None = None

    # Advanced comparison app
    policy_analyzer_url: str = "https://ashlar-policyanalyzer.up.railway.app/"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
