FROM python:3.12-slim
WORKDIR /app

# Requisitos
COPY etl/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY etl/worker.py .

# SQL del ETL (ahora relativos al context "..")
COPY db/migrations/110_txn_clean.sql sql/110_txn_clean.sql
COPY db/migrations/120_txn_agg.sql  sql/120_txn_agg.sql

CMD ["python", "worker.py"]
