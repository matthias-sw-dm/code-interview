from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Voucher API"
    debug: bool = True

    database_path: str = "vouchers.db"
    cors_origins: list[str] = ["http://localhost:3000"]

    jwt_secret: str = "dm-voucher-jwt-secret-2024"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60

    admin_email: str = "admin@voucher.local"
    admin_password: str = "Admin2024!"

    partner_webhook_secret: str = "partner-shared-secret"
    fraud_check_url: str = "http://localhost:9999/fraud/check"

    model_config = {"env_file": ".env"}


settings = Settings()
