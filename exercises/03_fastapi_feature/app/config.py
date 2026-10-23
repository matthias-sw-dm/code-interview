from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://interview:interview@localhost:5432/userdb"
    api_key: str = "secret-interview-key"

    model_config = {"env_file": ".env"}


settings = Settings()
