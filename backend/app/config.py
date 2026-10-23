from pathlib import Path
from urllib.parse import quote_plus

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_PATH = Path(__file__).resolve().parent.parent

MAX_FILE_SIZE = 10 * 1024 * 1024
UPLOAD_DIR = BASE_PATH / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
]


LOG_MAX_BYTES = 1024 * 1024
BACKUP_COUNT = 7


class Settings(BaseSettings):
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "123456"
    MYSQL_DATABASE: str = "database"

    JWT_SECRET_KEY: str = "sjQ9crUw71awph8ORnvERoUtMQ19qelECFjj06i1urz"
    JWT_EXPIRE_HOURS: int = 24
    JWT_ALGORITHM: str = "HS256"

    
    MODEL_PROVIDER: str = "deepseek"
    DEEPSEEK_API_KEY: str = "your despseek api key"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-flash"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        password = quote_plus(self.MYSQL_PASSWORD)
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{password}"
            # f"mysql+asyncmy://{self.MYSQL_USER}:{password}"     # 使用asyncmy异步驱动
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    model_config = SettingsConfigDict(
        env_file=BASE_PATH / ".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )


settings = Settings()
