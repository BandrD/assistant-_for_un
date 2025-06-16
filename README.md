# Assistant for UN
Система реализует мультиагентную архитектуру для обработки запросов студентов по учебным и административным вопросам. Она включает:

Этап обработки университетских документов (RAG-система)

Обработку запросов через мультиагентную систему

Планирование и автоматизацию обновления данных через Airflow

Мониторинг и трекинг через MLflow

```mermaid
flowchart TD
    %% ===== Этап 1: RAG-система =====
    subgraph RAG["Этап 1: RAG Core (Docker)"]
        D[University Docs] -->|"1 Загрузка (Docker Volume)"| TS[Text Splitter]
        TS -->|2 Разбивка на чанки| EG[Embedding Generator]
        EG -->|3 Сохранение| VDB[(VectorDB Chroma Faiss)]
        style VDB fill:#f9f,stroke:#333
    end

    %% ===== Клиентский запрос =====
    C[Client] -->|"POST /ask?type=exam (Когда сессия?)"| API[FastAPI]
    API -->|Route Request| A1[Agent 1: Routing]

    %% ===== Этап 2: Агенты =====
    subgraph MA["Этап 2: Multi-Agent"]
        ENV[Env: GIGACHAT_API_KEY] -->|"Load API Key"| A3
        A1 -->|"Учебные запросы"| Q1[(RabbitMQ search)]
        A1 -->|"Админ. запросы"| Q2[(RabbitMQ admin)]
        
        Q1 --> A2[Search Agent]
        Q2 --> A2
        A2 -->|"Поиск по эмбеддингам Логирование"| VDB
        A2 -->|"Контекст + метаданные"| Q3[(RabbitMQ gen)]
        
        Q3 --> A3[Generation Agent]
        A3 -->|"Промпт: Контекст История Шаблон"| LLM[(LLM: GigaChat)]
        LLM -->|Валидация ответа| A3
        A3 -->|Форматированный ответ| API
    end

    %% ===== Этап 3: Airflow =====
    subgraph AF["Этап 3: Airflow Pipeline"]
        DAG[Airflow DAG] -->|ingest_docs: Новые документы PDF Word парсинг| D
        DAG -->|reindex: Обновление индекса Оптимизация| VDB
        DAG -->|validate: Retry 3 попытки Проверка качества| LLM
        style DAG fill:#2c3,stroke:#333
    end

    %% ===== Этап 4: MLflow =====
    subgraph ML["Этап 4: MLflow Tracking"]
        A2 -->|Параметры Модель эмбеддингов Размер чанков| MLF[MLflow]
        A3 -->|Промпты Шаблоны Токены| MLF
        API -->|A/B тесты Стратегии поиска Модели LLM| MLF
        MLF -.->|Model Registry| A3
        style MLF fill:#78f,stroke:#333
    end

    %% ===== Стили =====
    style RAG fill:#fff2cc,stroke:#333
    style MA fill:#d5e8d4,stroke:#333
    style AF fill:#e1d5e7,stroke:#333
    style ML fill:#dae8fc,stroke:#333
```
