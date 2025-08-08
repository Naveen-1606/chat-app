from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Chat App"
    VERSION: str = "0.1.0"
    DATABASE_URL: str = "sqlite:///./chat.db"  # Replace with PostgreSQL later

    class Config:
        env_file = ".env"

settings = Settings()
