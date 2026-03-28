from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.5-flash-lite"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    top_k_default: int = 15

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
