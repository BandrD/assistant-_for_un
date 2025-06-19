FROM apache/airflow:2.9.1-python3.10

USER root
WORKDIR /app

COPY ./services/airflow/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./services/airflow/ /opt/airflow/dags/

USER airflow 
