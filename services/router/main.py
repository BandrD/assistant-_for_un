# services/router/main.py

import os
import json
import pika
import time

# Параметры подключения
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

def connect_to_rabbitmq(max_retries=10, delay=5):
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials
    )
    for attempt in range(max_retries):
        try:
            connection = pika.BlockingConnection(parameters)
            print("спешное подключение к RabbitMQ")
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Попытка подключения {attempt + 1} не удалась: {e}")
            if attempt < max_retries - 1:
                print(f"Повторная попытка через {delay} сек...")
                time.sleep(delay)
            else:
                raise RuntimeError("Не удалось подключиться к RabbitMQ после всех попыток")

def main():
    # Подключаемся к RabbitMQ
    connection = connect_to_rabbitmq()
    channel = connection.channel()

    # Объявляем очереди как durable
    channel.queue_declare(queue="incoming", durable=True)
    channel.queue_declare(queue="search", durable=True)
    channel.queue_declare(queue="admin", durable=True)

    print("outing Agent запущен, слушаем очередь 'incoming'...")

    # Callback-функция для обработки и роутинга
    def callback(ch, method, properties, body):
        msg = json.loads(body)
        # Роутим по полю type
        target_queue = "search" if msg.get("type") == "exam" else "admin"
        ch.basic_publish(
            exchange="",
            routing_key=target_queue,
            body=json.dumps(msg),
            properties=pika.BasicProperties(
                delivery_mode=2  # сделать сообщение persistent
            )
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"Routed request_id={msg.get('request_id')} to '{target_queue}'")

    # Подписываемся на очередь incoming
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="incoming", on_message_callback=callback)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Routing Agent остановлен вручную")
    finally:
        channel.close()
        connection.close()

if __name__ == "__main__":
    main()
