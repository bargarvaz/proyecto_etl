import json, os, time
from datetime import datetime
import pika, psycopg
from psycopg.rows import tuple_row

PG_DSN = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}" \
         f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
RMQ_HOST=os.getenv("RABBITMQ_HOST","rabbitmq"); RMQ_PORT=int(os.getenv("RABBITMQ_PORT","5672"))
RMQ_USER=os.getenv("RABBITMQ_USER","guest"); RMQ_PASS=os.getenv("RABBITMQ_PASSWORD","guest")
QUEUE=os.getenv("ETL_QUEUE","txn_etl"); DLX=os.getenv("ETL_DLX","dlx"); DLQ=os.getenv("ETL_DLQ","txn_etl.dlq")
PREFETCH=int(os.getenv("ETL_PREFETCH","200")); RETRY_MAX=int(os.getenv("ETL_RETRY_MAX","5"))

def mk_channel():
    creds = pika.PlainCredentials(RMQ_USER, RMQ_PASS)
    params = pika.ConnectionParameters(host=RMQ_HOST, port=RMQ_PORT, credentials=creds, heartbeat=30)
    conn = pika.BlockingConnection(params); ch = conn.channel()
    ch.exchange_declare(exchange=DLX, exchange_type="direct", durable=True)
    ch.queue_declare(queue=DLQ, durable=True); ch.queue_bind(queue=DLQ, exchange=DLX, routing_key=DLQ)
    ch.queue_declare(queue=QUEUE, durable=True, arguments={
        "x-dead-letter-exchange": DLX, "x-dead-letter-routing-key": DLQ,
    })
    ch.basic_qos(prefetch_count=PREFETCH)
    return conn, ch

def mk_pg(): return psycopg.connect(PG_DSN, autocommit=False)

def ack_next(ch, delivery_tag, next_msg):
    ch.basic_ack(delivery_tag)
    if next_msg:
        ch.basic_publish(exchange="", routing_key=QUEUE,
            body=json.dumps(next_msg).encode(),
            properties=pika.BasicProperties(delivery_mode=2))

def handle_stage(cur, payload):
    # Inserta al staging (puede venir del publisher o de otra fuente)
    cur.execute("""
      INSERT INTO etl.txn_stage (account_id, merchant_id, terminal_id, amount, currency, status, created_at)
      VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (payload["account_id"], payload["merchant_id"], payload["terminal_id"],
          float(payload["amount"]), payload["currency"], payload["status"],
          datetime.fromisoformat(payload["created_at"])))
    return {"step":"clean"}

def handle_clean(cur, payload):
    # Ejecuta SQL clean
    cur.execute(open("/app/sql/110_txn_clean.sql").read())
    return {"step":"agg"}

def handle_agg(cur, payload):
    cur.execute(open("/app/sql/120_txn_agg.sql").read())
    return None

def on_message(ch, method, props, body):
    headers = props.headers or {}; retry = int(headers.get("x-retry",0))
    delivery_tag = method.delivery_tag
    try:
        msg = json.loads(body)
        step = msg.get("step","stage")
        with mk_pg() as conn:
            with conn.cursor(row_factory=tuple_row) as cur:
                if step=="stage":
                    nxt = handle_stage(cur, msg)
                elif step=="clean":
                    nxt = handle_clean(cur, msg)
                elif step=="agg":
                    nxt = handle_agg(cur, msg)
                else:
                    raise ValueError(f"Unknown step: {step}")
            conn.commit()
        ack_next(ch, delivery_tag, nxt)
    except Exception as e:
        if retry + 1 >= RETRY_MAX:
            ch.basic_publish(exchange=DLX, routing_key=DLQ, body=body,
                properties=pika.BasicProperties(delivery_mode=2,
                    headers={"x-error": str(e)[:500], "x-retry": retry+1}))
            ch.basic_ack(delivery_tag)
        else:
            ch.basic_publish(exchange="", routing_key=QUEUE, body=body,
                properties=pika.BasicProperties(delivery_mode=2, headers={"x-retry": retry+1}))
            ch.basic_ack(delivery_tag)

def main():
    # Copia los SQL al contenedor (ya están montados en /app/sql por Dockerfile)
    conn, ch = mk_channel()
    ch.basic_consume(queue=QUEUE, on_message_callback=on_message, auto_ack=False)
    print("ETL encadenado listo (stage→clean→agg).")
    try: ch.start_consuming()
    except KeyboardInterrupt:
        ch.stop_consuming(); conn.close()

if __name__ == "__main__":
    main()
