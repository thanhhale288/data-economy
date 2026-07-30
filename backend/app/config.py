from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/mfg_economy.db"
    redis_url: str = "redis://localhost:6379/0"
    app_name: str = "Manufacturing Data Economy"
    debug: bool = True


settings = Settings()
