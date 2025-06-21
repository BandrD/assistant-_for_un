FROM apache/airflow:2.9.1-python3.10

USER airflow
WORKDIR /app

RUN airflow version

COPY ./dags/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./dags /opt/airflow/dags/
