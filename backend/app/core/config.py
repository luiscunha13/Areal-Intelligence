import os

try:
    from pydantic_settings import BaseSettings
    class Settings(BaseSettings):
        fred_api_key: str | None = "868279625b6901f8cb13f6758476ccc8"
        database_url: str = "sqlite:///./macrodb.sqlite"

        class Config:
            env_file = ".env"
            extra = "ignore"
except ImportError:
    class Settings:
        fred_api_key: str | None = os.getenv("FRED_API_KEY", "868279625b6901f8cb13f6758476ccc8")
        database_url: str = os.getenv("DATABASE_URL", "sqlite:///./macrodb.sqlite")

settings = Settings()
