from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, чтобы не хардкодить параметры подклбючения к базе данныъх"""
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int


settings = Settings()