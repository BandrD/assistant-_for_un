from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from document_processor import DocumentProcessor
import os

def ingest_docs():
    processor = DocumentProcessor()
    doc_dir = "/data/docs"
    for file in os.listdir(doc_dir):
        processor.process_document(os.path.join(doc_dir, file), file, "schedule")

def reindex():
    processor = DocumentProcessor()
    processor.client.delete_collection("university_docs")
    ingest_docs()

def validate():
    # Пример валидации
    pass

with DAG(
    "university_pipeline",
    start_date=datetime(2025, 6, 21),
    schedule_interval="@daily",
) as dag:
    ingest_task = PythonOperator(task_id="ingest_docs", python_callable=ingest_docs)
    reindex_task = PythonOperator(task_id="reindex", python_callable=reindex)
    validate_task = PythonOperator(task_id="validate", python_callable=validate)

    ingest_task >> reindex_task >> validate_task
