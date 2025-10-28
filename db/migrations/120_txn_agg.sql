CREATE TABLE IF NOT EXISTS etl.txn_daily_agg (
  day date NOT NULL,
  merchant_id uuid NOT NULL,
  txn_count bigint NOT NULL,
  total_amount numeric(18,2) NOT NULL,
  PRIMARY KEY (day, merchant_id)
);

INSERT INTO etl.txn_daily_agg (day, merchant_id, txn_count, total_amount)
SELECT date_trunc('day', created_at)::date AS day,
       merchant_id,
       count(*) AS txn_count,
       sum(amount)::numeric(18,2) AS total_amount
FROM payments.txn
GROUP BY 1,2
ON CONFLICT (day, merchant_id) DO UPDATE
SET txn_count = EXCLUDED.txn_count,
    total_amount = EXCLUDED.total_amount;
