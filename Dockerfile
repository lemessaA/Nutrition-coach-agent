# API image: run from repository root
#   docker build -t nutrition-coach-api .
#   docker run --rm -p 8000:8000 --env-file .env nutrition-coach-api
#
# See docker-compose.yml for API + PostgreSQL.

FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Optional: minimal build tools if a wheel is missing (uncomment if pip install fails)
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
#     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app_entry.py .
COPY backend/ ./backend/
COPY data/ ./data/

RUN mkdir -p /app/backend/uploads

EXPOSE 8000

# One worker is typical behind a reverse proxy; increase for CPU-bound loads
CMD ["uvicorn", "app_entry:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
