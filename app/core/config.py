from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # -----------------------------
    # Database & Auth
    # -----------------------------
    database_url: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    # -----------------------------
    # Frontend
    # -----------------------------
    frontend_url: str              # used for email verification links
    frontend_origins: str          # used for CORS

    # -----------------------------
    # Email / SMTP
    # -----------------------------
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    email_from: str
    brevo_api_key: str | None = None

    class Config:
        env_file = ".env"

# Load settings
settings = Settings()


