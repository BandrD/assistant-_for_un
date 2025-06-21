# services/api/main.py
from fastapi import FastAPI
import pika
import json
import uuid
import os

app = FastAPI()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))

@app.post("/ask")
async def ask_question(question: str, type: str = "exam"):
    request_id = str(uuid.uuid4())
    message = {"request_id": request_id, "question": question, "type": type}

    # Отправляем запрос в RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
    )
    channel = connection.channel()
    channel.queue_declare(queue="search")
    channel.basic_publish(exchange="", routing_key="search", body=json.dumps(message))
    connection.close()

    # Здесь можно добавить логику ожидания ответа через callback очередь
    return {"request_id": request_id, "status": "queued"}
