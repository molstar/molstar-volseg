from pathlib import Path
from pydantic import BaseSettings

class _Settings(BaseSettings):
    HOST: str = '0.0.0.0'
    PORT: int = 9000
    DEV_MODE: bool = False
    DB_PATH: Path = Path(__file__).absolute().parent.parent / "db"


settings = _Settings()