-- 001_partitions.sql
DO $$
DECLARE
  start_date date := date '2024-01-01';
  end_date   date := date '2026-01-01';
  cur date := start_date;
BEGIN
  WHILE cur < end_date LOOP
    EXECUTE format($f$
      CREATE TABLE IF NOT EXISTS payments.txn_%s
      PARTITION OF payments.txn
      FOR VALUES FROM (%L) TO (%L);
    $f$, to_char(cur, 'YYYYMM'), cur, (cur + INTERVAL '1 month')::date);
    cur := (cur + INTERVAL '1 month')::date;
  END LOOP;
END $$;
