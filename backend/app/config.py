from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "BunkWise-AI Backend"
    database_url: str = "sqlite:///./bunkwise.db"
    default_state_code: str = "BR"
    gemini_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
