"""Fachada de mensajería: elige la implementación según MESSAGE_BROKER.

`app/main.py` y `worker.py` importan `publish_lead`/`consume_leads` de este
módulo sin saber si por debajo corre RabbitMQ (app/queue_rabbitmq.py) o
Kafka (app/queue_kafka.py) — mismo contrato, backend intercambiable.
"""
from app.config import settings

if settings.message_broker == "kafka":
    from app.queue_kafka import consume_leads, publish_lead
else:
    from app.queue_rabbitmq import consume_leads, publish_lead

__all__ = ["publish_lead", "consume_leads"]
