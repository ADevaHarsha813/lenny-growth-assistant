FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 300 --retries 5 fastapi uvicorn pydantic sqlalchemy asyncpg alembic python-dotenv
RUN pip install --no-cache-dir --timeout 300 --retries 5 anthropic httpx tenacity structlog
RUN pip install --no-cache-dir --timeout 300 --retries 5 chromadb tiktoken
RUN pip install --no-cache-dir --timeout 300 --retries 5 pytest pytest-asyncio

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
