FROM python:3.10-slim

WORKDIR /app

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./main.py .
COPY ./document_processor.py .

CMD ["python", "main.py"]
