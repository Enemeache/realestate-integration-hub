from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "propleads"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    leads_queue: str = "leads.incoming"
    anthropic_api_key: str | None = None
    embedding_engine: str = "tfidf"  # "tfidf" (default, scikit-learn) or "sentence-transformers"
    log_level: str = "INFO"
    webhook_secret: str | None = None  # si se configura, /webhook/lead exige firma HMAC valida
    message_broker: str = "rabbitmq"  # "rabbitmq" o "kafka" (ver app/broker.py)
    kafka_bootstrap_servers: str = "localhost:9092"

    class Config:
        env_file = ".env"


settings = Settings()
