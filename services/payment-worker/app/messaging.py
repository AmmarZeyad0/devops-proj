import json
import logging
import time

import pika

from app.config import settings

logger = logging.getLogger("messaging")

EXCHANGE = "tickets_exchange"


def _connect():
    return pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))


def publish_event(channel, routing_key: str, payload: dict) -> None:
    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key=routing_key,
        body=json.dumps(payload, default=str),
        properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
    )


def run_consumer(queue_name: str, handlers: dict) -> None:
    """Blocking pika consumer loop, retrying if the broker isn't up yet. This is the worker's main loop.

    One queue is bound to every routing key in `handlers`; each message is dispatched to the
    handler for the key it arrived with.
    """
    while True:
        try:
            connection = _connect()
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
            channel.queue_declare(queue=queue_name, durable=True)
            for routing_key in handlers:
                channel.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key=routing_key)

            def _callback(ch, method, properties, body):
                try:
                    handlers[method.routing_key](ch, json.loads(body))
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception:
                    logger.exception("Failed to process message on %s", method.routing_key)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue_name, on_message_callback=_callback)
            logger.info("Consuming %s -> queue %s", ", ".join(handlers), queue_name)
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            logger.warning("RabbitMQ not reachable yet, retrying in 5s...")
            time.sleep(5)
