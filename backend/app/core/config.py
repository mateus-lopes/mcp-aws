from pathlib import Path
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    OAUTH_CLIENT_ID: str = "mcp-aws-gpt"
    OAUTH_CLIENT_SECRET: str = ""
    OAUTH_ALLOWED_REDIRECT_URIS: str = ""
    OAUTH_AUTH_CODE_EXPIRE_MINUTES: int = 10
    OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    PUBLIC_BASE_URL: str = ""

    class Config:
        env_file = str(ROOT_DIR / ".env")


settings = Settings()
