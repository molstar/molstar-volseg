from pathlib import Path
from pydantic_settings import BaseSettings


class _Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 4500
    DEV_MODE: bool = False
    DB_PATH: Path = Path("preprocessor/temp/test_db")
    GIT_TAG: str = ""
    GIT_SHA: str = ""


settings = _Settings()
