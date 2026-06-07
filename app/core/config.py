from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Jarvis Backend"
    environment: str = "development"


settings = Settings()