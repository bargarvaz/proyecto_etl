CREATE SCHEMA IF NOT EXISTS etl;

-- staging (sin FKs; validaremos en 'clean')
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
