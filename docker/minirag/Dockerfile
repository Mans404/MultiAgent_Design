FROM ghcr.io/astral-sh/uv:0.6.14-python3.10-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libavif-dev pkg-config \
    libjpeg-dev \
    gcc unzip zip \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY src/requirements.txt .

ENV UV_HTTP_TIMEOUT=300
RUN uv pip install -r requirements.txt --system --index-url https://mirrors.aliyun.com/pypi/simple/
    
COPY src/ .

# Create directory structure for alembic

RUN mkdir -p /app/models/db_schemes/mini_rag

COPY docker/minirag/alembic.ini /app/models/db_schemes/mini_rag/alembic.ini
COPY docker/minirag/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]