import pika
import json
import os
import time

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
            print("Успешное подключение к RabbitMQ")
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Попытка подключения {attempt + 1} не удалась: {e}")
            if attempt < max_retries - 1:
                print(f"Повторная попытка через {delay} секунд...")
                time.sleep(delay)
            else:
                raise Exception("Не удалось подключиться к RabbitMQ после максимального количества попыток")

def callback(ch, method, properties, body):
    message = json.loads(body)
    question = message["question"]
    model = "gigachat" if "exam" in question.lower() else "yandexgpt"
    message["model"] = model
    ch.basic_publish(
        exchange="",
        routing_key="questions",
        body=json.dumps(message)
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    try:
        connection = connect_to_rabbitmq()
        channel = connection.channel()
        channel.queue_declare(queue="input")
        channel.queue_declare(queue="questions")
        channel.basic_consume(queue="input", on_message_callback=callback)
        print("Роутер запущен, ожидание сообщений...")
        channel.start_consuming()
    except Exception as e:
        print(f"Ошибка в роутере: {e}")
        raise

if __name__ == "__main__":
    main()
