FROM python:3.10-slim

WORKDIR /app

COPY ./services/router/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./services/router/ .

CMD ["python", "main.py"]
