from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Runtime mode
    DEMO_MODE: bool = True
    FRONTEND_ORIGINS: str = "http://localhost:3000,http://localhost:19006"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://synapse:password@localhost:5432/synapse"
    REDIS_URL: str = "redis://localhost:6379/0"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "adminpassword"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    # AI
    GEMINI_API_KEY: str = ""
    GEMINI_FLASH_MODEL: str = "gemini-2.0-flash"
    GEMINI_PRO_MODEL: str = "gemini-1.5-pro"

    # Tavily
    TAVILY_API_KEY: Optional[str] = None

    # Coqui TTS (open-source, runs locally, no API key required)
    COQUI_TTS_MODEL: str = "tts_models/en/ljspeech/tacotron2-DCA"

    # Auth
    JWT_SECRET_KEY: str = "changeme-in-production"
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None

    # Integrations
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    SLACK_CLIENT_ID: Optional[str] = None
    SLACK_CLIENT_SECRET: Optional[str] = None
    SPLITWISE_API_KEY: Optional[str] = None
    INTEGRATION_ENCRYPTION_KEY: Optional[str] = None

    # Delivery
    ONESIGNAL_APP_ID: Optional[str] = None
    ONESIGNAL_REST_API_KEY: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None

    # Blockchain
    POLYGON_AMOY_RPC_URL: str = "https://rpc-amoy.polygon.technology"
    DEPLOYER_PRIVATE_KEY: Optional[str] = None
    AGREEMENT_REGISTRY_ADDRESS: Optional[str] = None

    # Monitoring
    SENTRY_DSN: Optional[str] = None

settings = Settings()
