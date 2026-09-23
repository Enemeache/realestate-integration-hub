"""Publisher/consumer sobre Kafka (kafka-python).

Mismo contrato que app/queue_rabbitmq.py (publish_lead/consume_leads),
elegible con la env var MESSAGE_BROKER=kafka. Sirve para mostrar que el
pipeline no está atado a una tecnología de mensajería puntual: RabbitMQ
resuelve bien "cola de tareas" (un mensaje, un consumidor, reintentar si
falla); Kafka tiene sentido cuando varios consumidores independientes
necesitan leer el mismo stream de eventos (ej. este mismo lead también
alimentando analytics o un CRM, además del worker de matching).
"""
from __future__ import annotations

import json
import logging
from typing import Callable

from kafka import KafkaConsumer, KafkaProducer

from app.config import settings

logger = logging.getLogger(__name__)


def publish_lead(payload: dict) -> None:
    producer = KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    try:
        future = producer.send(settings.leads_queue, value=payload)
        future.get(timeout=10)
        logger.info("Lead publicado en el topic %s (Kafka)", settings.leads_queue)
    finally:
        producer.close()


def consume_leads(handler: Callable[[dict], None]) -> None:
    consumer = KafkaConsumer(
        settings.leads_queue,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        enable_auto_commit=False,
        group_id="propleads-workers",
    )
    logger.info("Worker esperando leads en el topic %s (Kafka)", settings.leads_queue)
    for message in consumer:
        try:
            handler(message.value)
            consumer.commit()
        except Exception:
            logger.exception("Error procesando lead, no se hace commit (se reprocesa en el proximo poll)")
