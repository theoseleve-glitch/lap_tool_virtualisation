from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TRACKRECO_")

    app_name: str = "trackreco-layout-registry"
    environment: str = "dev"
    api_prefix: str = "/api/v1"

    postgres_dsn: str = "postgresql+psycopg://trackreco:trackreco@localhost:5432/trackreco"
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "trackreco-artifacts"
    s3_region: str = "eu-west-3"

    log_level: str = "INFO"


settings = Settings()
