"""Runtime configuration. Every value comes from the environment, nothing hidden."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRAWLER_", env_file=".env", extra="ignore")

    secret: str = ""
    token_ttl: int = 3600
    max_downloads: int = 4
    max_probes: int = 8
    cors_origins: str = "http://localhost:3000"
    public_origin: str = "http://localhost:3000"
    cookies_file: str = ""
    rate_probe: int = 12
    rate_media: int = 20
    rate_preview: int = 240
    rate_read: int = 120
    rate_mcp: int = 60
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
