from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Business Process Automation"
    database_url: str = "sqlite:///./automation.db"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    notification_webhook_url: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
