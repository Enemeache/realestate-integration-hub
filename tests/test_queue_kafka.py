"""Tests unitarios del backend Kafka: mockean KafkaProducer/KafkaConsumer,
no requieren un broker real corriendo (igual criterio que con RabbitMQ:
la infra real se prueba con docker-compose, no en CI)."""
from unittest.mock import MagicMock, patch

from app.queue_kafka import consume_leads, publish_lead


def test_publish_lead_sends_and_flushes():
    fake_future = MagicMock()
    fake_producer = MagicMock()
    fake_producer.send.return_value = fake_future

    with patch("app.queue_kafka.KafkaProducer", return_value=fake_producer) as mock_cls:
        publish_lead({"id": "lead-1", "message": "hola"})

    mock_cls.assert_called_once()
    fake_producer.send.assert_called_once()
    kwargs = fake_producer.send.call_args[1]
    assert kwargs["value"] == {"id": "lead-1", "message": "hola"}
    fake_future.get.assert_called_once()
    fake_producer.close.assert_called_once()


def test_consume_leads_commits_after_successful_handler():
    fake_message = MagicMock(value={"id": "lead-2"})
    fake_consumer = MagicMock()
    fake_consumer.__iter__.return_value = iter([fake_message])
    handled = []

    with patch("app.queue_kafka.KafkaConsumer", return_value=fake_consumer):
        consume_leads(lambda payload: handled.append(payload))

    assert handled == [{"id": "lead-2"}]
    fake_consumer.commit.assert_called_once()


def test_consume_leads_skips_commit_when_handler_fails():
    fake_message = MagicMock(value={"id": "lead-3"})
    fake_consumer = MagicMock()
    fake_consumer.__iter__.return_value = iter([fake_message])

    def _boom(_payload):
        raise ValueError("fallo simulado")

    with patch("app.queue_kafka.KafkaConsumer", return_value=fake_consumer):
        consume_leads(_boom)

    fake_consumer.commit.assert_not_called()
