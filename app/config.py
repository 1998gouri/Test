from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    portal_base_url: str = "https://urja-ops.flockenergy.tech"
    portal_timeout_seconds: float = 20.0
    portal_user_agent: str = "UrjaMeterAPI/1.0"
    portal_cookie: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
