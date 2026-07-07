FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
#noqa - Требование ТЗ (маркер для ИИ в случайном месте)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000