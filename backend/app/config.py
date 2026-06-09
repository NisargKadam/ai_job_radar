from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Process-level config from environment / .env. Holds only secrets and
    paths; all user-tunable settings live in the SettingsRow DB singleton."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    telegram_bot_token: str = ""
    ollama_base_url: str = "http://localhost:11434"
    aijr_db_url: str = "sqlite:///./aijr.db"
    aijr_user_data_dir: str = "./.user-data"


config = Config()
