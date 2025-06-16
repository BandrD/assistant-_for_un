# Assistant
Система реализует мультиагентную архитектуру для обработки запросов студентов по учебным и административным вопросам. Она включает:

Этап обработки университетских документов (RAG-система)

Обработку запросов через мультиагентную систему

Планирование и автоматизацию обновления данных через Airflow

Мониторинг и трекинг через MLflow

```mermaid
flowchart TD
    %% ===== Этап 1: RAG-система =====
    subgraph RAG["Этап 1: RAG Core (Docker)"]
        D[University Docs] -->|"Загрузка (Docker Volume)"| TS[Text Splitter]
        TS -->|Разбивка на чанки| EG[Embedding Generator]
        EG -->|Сохранение| VDB[(VectorDB Chroma or Faiss)]
        style VDB fill:#f9f,stroke:#333
    end

    %% ===== Клиентский запрос =====
    C[Client] -->|"POST /ask?type=exam (Когда сессия?)"| API[FastAPI]
    API -->|Route Request| A1[Routing Agent]

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
## Полный цикл обработки запроса

```mermaid
sequenceDiagram
    Client->>FastAPI: POST /ask?type=exam
    FastAPI->>Routing Agent: Запрос
    Router->>RabbitMQ: В очередь учебных запросов
    RabbitMQ->>Search Agent: Задание
    Search Agent->>VectorDB: Поиск контекста
    VectorDB-->>Search Agent: 3 чанка
    Search Agent->>RabbitMQ: Контекст → очередь gen
    RabbitMQ->>Generator: Задание
    Generator->>LLM: Промпт + контекст
    LLM-->>Generator: Ответ
    Generator->>FastAPI: Ответ
    FastAPI->>Client: JSON
```

## Этап 1: RAG-система 

### University Docs → Text Splitter
Университетские документы (PDF, Word) монтируются внутрь контейнера через Docker volume.
Это могут быть расписания, регламенты, инструкции и другие официальные документы.

### Text Splitter → Embedding Generator
Документы разбиваются на смысловые фрагменты (чанки), пригодные для векторизации.
Применяется логика нарезки по абзацам, предложениям или по токенам.

### Embedding Generator → VectorDB
Генератор эмбеддингов преобразует каждый чанк в вектор с использованием предобученной модели (например, sentence-transformers).
Вектора сохраняются в базу данных (Chroma или Faiss), где они индексируются по смыслу и метаданным

## Этап 2: Мультиагентная архитектура
### Client → FastAPI
Студент отправляет запрос в веб-интерфейс (например, "Когда сессия?")
HTTP-запрос содержит параметр type=exam, по которому будет определяться категория.

### FastAPI → Routing Agent
API передаёт запрос агенту маршрутизации.
Агент 1 (Routing) анализирует тему и категорию запроса.

### Routing Agent → RabbitMQ (search/admin)
Запрос классифицируется как учебный или административный.

В зависимости от категории он отправляется в соответствующую очередь RabbitMQ:
search — расписание, экзамены и т.д.
admin — справки, заявления, процедуры.

### RabbitMQ → Search Agent
Агент 2 (Search) подписан на обе очереди и подхватывает сообщения.
Он различает тип запроса по метаданным и выполняет поиск по нужной части VectorDB.

### Search Agent → VectorDB
Производится семантический поиск по базе эмбеддингов.
В лог пишется информация о выполненном поиске и источнике данных.

### Search Agent → RabbitMQ (gen)
Найденный контекст (чанки) и сопутствующие данные (метки, источник, дата) отправляются в очередь генерации.

### RabbitMQ → Generation Agent
Агент 3 (Generation) получает контекст и генерирует персонализированный ответ.

### Generation Agent → LLM
LLM (GigaChat или YandexGPT) вызывается через API (ключ загружается из ENV).
Возвращается сгенерированный текст.

### LLM → Generation Agent
Ответ LLM валидируется (на соответствие шаблону, длине, правилам этики).

### Generation Agent → FastAPI
Финальный ответ от агента возвращается клиенту.

## Этап 3: Airflow пайплайн 

### Airflow → University Docs
DAG ingest_docs запускается по расписанию или триггеру.
Подгружаются новые PDF, DOCX и другие источники.

### Airflow → VectorDB
DAG reindex пересчитывает и оптимизирует индекс в VectorDB.
Это позволяет удалять устаревшие данные и ускорять поиск.

### Airflow → LLM
DAG validate делает контрольный прогон ответов LLM.
При неудаче включается retry-механизм (например, до 3 попыток).

## Этап 4: MLflow трекинг 

### Search Agent → MLflow
Логируются параметры генерации эмбеддингов: модель, размер чанков, стратегия нарезки.

### Generation Agent → MLflow
Фиксируются используемые промпты, шаблоны, длина ответа и количество токенов.

### FastAPI → MLflow
При A/B тестировании: сравнение качества разных стратегий поиска или LLM.

### MLflow → Model Registry → Generation Agent
Подтверждённые шаблоны и конфигурации можно выносить в Model Registry и загружать в Prod
