from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/weather_db"
    WEATHER_API_KEY: str = "mock_key"
    RATE_LIMIT_PER_MINUTE: int = 30

    class Config:
        env_file = ".env"

settings = Settings()