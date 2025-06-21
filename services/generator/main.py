import pika
import json
import os
import time
from save_prompt import save_prompt_to_mlflow

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
GIGACHAT_API_KEY = os.getenv("GIGACHAT_API_KEY")
YANDEXGPT_API_KEY = os.getenv("YANDEXGPT_API_KEY")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")

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
    model = message.get("model", "gigachat")
    prompt = f"Вопрос: {question}"
    response = "Mock response"  # Замените на реальный вызов модели
    save_prompt_to_mlflow(prompt, response, model)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    try:
        connection = connect_to_rabbitmq()
        channel = connection.channel()
        channel.queue_declare(queue="gen")
        channel.basic_consume(queue="gen", on_message_callback=callback)
        print("Генератор запущен, ожидание сообщений...")
        channel.start_consuming()
    except Exception as e:
        print(f"Ошибка в генераторе: {e}")
        raise

if __name__ == "__main__":
    main()
