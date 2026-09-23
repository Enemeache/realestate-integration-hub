"""Publisher/consumer sobre RabbitMQ (pika).

Simula el patrón real de integración pedido en el puesto: el webhook no
procesa el lead en el request (evita timeouts, permite reintentos), lo
publica en una cola y un worker separado lo consume de forma asíncrona.
"""
from __future__ import annotations

import json
import logging
from typing import Callable

import pika

from app.config import settings

logger = logging.getLogger(__name__)


def publish_lead(payload: dict) -> None:
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    try:
        channel = connection.channel()
        channel.queue_declare(queue=settings.leads_queue, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=settings.leads_queue,
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
        )
        logger.info("Lead publicado en la cola %s", settings.leads_queue)
    finally:
        connection.close()


def consume_leads(handler: Callable[[dict], None]) -> None:
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    channel = connection.channel()
    channel.queue_declare(queue=settings.leads_queue, durable=True)

    def _on_message(ch, method, _properties, body):
        try:
            handler(json.loads(body))
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            logger.exception("Error procesando lead, se descarta el mensaje")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=settings.leads_queue, on_message_callback=_on_message)
    logger.info("Worker esperando leads en la cola %s", settings.leads_queue)
    channel.start_consuming()
