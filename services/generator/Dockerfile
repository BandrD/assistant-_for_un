FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./main.py .
COPY ./save_prompt.py .

CMD ["python", "main.py"]
