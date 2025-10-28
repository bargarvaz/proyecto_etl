#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[1/4] Levantando infraestructura…"
cd compose
docker compose up -d

echo "[2/4] Esperando Postgres…"
until docker exec -i etl_postgres pg_isready -U pguser -d payments >/dev/null 2>&1; do
  sleep 1
done

echo "[3/4] Asegurando staging y agregados…"
docker exec -i etl_postgres psql -U pguser -d payments <<'SQL'
CREATE SCHEMA IF NOT EXISTS etl;
CREATE TABLE IF NOT EXISTS etl.txn_stage (
  id bigserial PRIMARY KEY,
  account_id uuid,
  merchant_id uuid,
  terminal_id uuid,
  amount numeric(12,2),
  currency text,
  status text,
  created_at timestamptz,
  loaded_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS etl.txn_daily_agg (
  day date NOT NULL,
  merchant_id uuid NOT NULL,
  txn_count bigint NOT NULL,
  total_amount numeric(18,2) NOT NULL,
  PRIMARY KEY (day, merchant_id)
);
SQL

echo "[4/4] Verificando servicios…"
docker compose ps
echo "Listo. Puedes publicar mensajes con: python3 ./scripts/publish.py"
