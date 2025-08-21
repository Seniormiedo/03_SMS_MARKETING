FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias del sistema mínimas para clientes de PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python primero (mejor cache)
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el resto del código
COPY . .

# Usuario no root
RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Directorio de trabajo
WORKDIR /app

# Comando por defecto (sobrescrito por docker compose)
CMD ["python", "main.py", "--interactive"]


