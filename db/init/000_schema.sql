-- 000_schema.sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS payments;

CREATE TABLE IF NOT EXISTS payments.account (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS payments.merchant (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL
);

CREATE TABLE IF NOT EXISTS payments.terminal (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id uuid NOT NULL REFERENCES payments.merchant(id) ON DELETE CASCADE,
  location text
);

CREATE TABLE IF NOT EXISTS payments.txn (
  id bigserial PRIMARY KEY,
  account_id uuid NOT NULL REFERENCES payments.account(id) ON DELETE CASCADE,
  merchant_id uuid NOT NULL REFERENCES payments.merchant(id),
  terminal_id uuid REFERENCES payments.terminal(id),
  amount numeric(12,2) NOT NULL,
  currency text NOT NULL DEFAULT 'MXN',
  status text NOT NULL DEFAULT 'ok',
  created_at timestamptz NOT NULL
) PARTITION BY RANGE (created_at);

CREATE INDEX IF NOT EXISTS idx_txn_account_created ON payments.txn (account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_txn_merchant_created ON payments.txn (merchant_id, created_at DESC);
