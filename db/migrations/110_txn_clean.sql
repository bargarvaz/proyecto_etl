-- limpia/valida y carga al destino final
WITH valid AS (
  SELECT s.*
  FROM etl.txn_stage s
  JOIN payments.account  a ON a.id  = s.account_id
  JOIN payments.merchant m ON m.id  = s.merchant_id
  JOIN payments.terminal t ON t.id  = s.terminal_id
  WHERE s.amount > 0 AND s.currency = 'MXN' 
    AND s.status IN ('ok','reversed','declined')
    AND s.created_at IS NOT NULL
)
INSERT INTO payments.txn (account_id, merchant_id, terminal_id, amount, currency, status, created_at)
SELECT account_id, merchant_id, terminal_id, amount, currency, status, created_at
FROM valid;
