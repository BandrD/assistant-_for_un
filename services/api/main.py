from fastapi import FastAPI
import pika
import json
import uuid
import os

app = FastAPI()


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
)
channel = connection.channel()

channel.queue_declare(queue="incoming", durable=True)

@app.post("/ask")
async def ask_question(question: str, type: str = "exam"):
    """
    Принимает вопрос от пользователя и публикует
    его в очередь 'incoming' для дальнейшей маршрутизации.
    """
    request_id = str(uuid.uuid4())
    payload = {
        "request_id": request_id,
        "question": question,
        "type": type
    }

    channel.basic_publish(
        exchange="",
        routing_key="incoming",
        body=json.dumps(payload),
        properties=pika.BasicProperties(
            delivery_mode=2  # сохранять сообщение на диск (durable)
        )
    )

    return {
        "request_id": request_id,
        "status": "queued",
        "queue": "incoming"
    }
