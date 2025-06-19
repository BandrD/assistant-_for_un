FROM python:3.10-slim

WORKDIR /app

COPY ./services/search/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./services/search/ .

CMD ["python", "main.py"]
