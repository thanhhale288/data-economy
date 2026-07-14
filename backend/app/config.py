from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/mfg_economy.db"
    redis_url: str = "redis://localhost:6379/0"
    app_name: str = "Manufacturing Data Economy"
    debug: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
