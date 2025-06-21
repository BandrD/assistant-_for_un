import pika
import json
import os
import time
from document_processor import DocumentProcessor

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))

def connect_to_rabbitmq(max_retries=10, delay=5):
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
    for attempt in range(max_retries):
        try:
            connection = pika.BlockingConnection(parameters)
            print("Успешное подключение к RabbitMQ")
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Попытка {attempt + 1} не удалась: {e}")
            if attempt < max_retries - 1:
                print(f"Повторная попытка через {delay} секунд...")
                time.sleep(delay)
            else:
                raise Exception("Не удалось подключиться к RabbitMQ")

def callback(ch, method, properties, body):
    message = json.loads(body)
    request_id = message["request_id"]
    question = message["question"]

    processor = DocumentProcessor()
    query_embedding = processor.model.encode([question])[0]
    results = processor.collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=3
    )

    context = results["documents"][0]
    metadata = results["metadatas"][0]

    gen_message = {
        "request_id": request_id,
        "question": question,
        "context": context,
        "metadata": metadata
    }
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
    )
    channel = connection.channel()
    channel.queue_declare(queue="gen")
    channel.basic_publish(exchange="", routing_key="gen", body=json.dumps(gen_message))
    connection.close()

    ch.basic_ack(delivery_tag=method.delivery_tag)

connection = connect_to_rabbitmq()
channel = connection.channel()
channel.queue_declare(queue="search")
channel.queue_declare(queue="admin")
channel.basic_consume(queue="search", on_message_callback=callback)
channel.basic_consume(queue="admin", on_message_callback=callback)
channel.start_consuming()
