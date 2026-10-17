from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["local", "prod"] = "local"
    database_url: str
    test_database_url: str | None = None
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120
    wechat_appid: str = ""
    wechat_secret: str = ""
    merchant_openid: str = ""  # 命中此 openid 的用户 role 为 merchant
    upload_dir: str = "var/uploads"
    upload_base_url: str = "/static"


settings = Settings()
