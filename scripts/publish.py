import os, json, random, datetime, uuid
import pika, psycopg

PG_DSN = "postgresql://pguser:pgpass@localhost:5432/payments"
RMQ_HOST="localhost"; RMQ_PORT=5672; RMQ_USER="guest"; RMQ_PASS="guest"
QUEUE=os.getenv("ETL_QUEUE","txn_etl")

def fetch_ids():
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM payments.account LIMIT 50000")
            accounts=[r[0] for r in cur.fetchall()]
            cur.execute("SELECT id, merchant_id FROM payments.terminal LIMIT 10000")
            terminals=cur.fetchall()
    return accounts, terminals

def publish(n=10000):
    accounts, terminals = fetch_ids()
    creds = pika.PlainCredentials(RMQ_USER, RMQ_PASS)
    params = pika.ConnectionParameters(host=RMQ_HOST, port=RMQ_PORT, credentials=creds)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # 🧩 Asegura la cola con la MISMA configuración que el worker
    ch.exchange_declare(exchange="dlx", exchange_type="direct", durable=True)
    ch.queue_declare(queue="txn_etl.dlq", durable=True)
    ch.queue_bind(queue="txn_etl.dlq", exchange="dlx", routing_key="txn_etl.dlq")

    ch.queue_declare(
        queue=QUEUE,
        durable=True,
        arguments={
            "x-dead-letter-exchange": "dlx",
            "x-dead-letter-routing-key": "txn_etl.dlq",
        }
    )

    statuses=["ok","reversed","declined"]
    for i in range(n):
        acc = str(random.choice(accounts))           # 👈 convierte UUID a string
        term_id, merch_id = random.choice(terminals)
        term_id = str(term_id)
        merch_id = str(merch_id)
        msg = {
            "account_id": acc,
            "merchant_id": merch_id,
            "terminal_id": term_id,
            "amount": round(random.uniform(1, 500), 2),
            "currency": "MXN",
            "status": random.choices(statuses, weights=[92,5,3], k=1)[0],
            "created_at": (datetime.datetime(2024,1,1) + datetime.timedelta(
                           days=random.randint(0, 630),
                           seconds=random.randint(0, 86399))
                          ).strftime("%Y-%m-%d %H:%M:%S")
        }
        ch.basic_publish(
            exchange="",
            routing_key=QUEUE,
            body=json.dumps(msg).encode(),   # ahora sí se puede serializar
            properties=pika.BasicProperties(delivery_mode=2)
        )
        if (i+1) % 1000 == 0:
            print(f"Publicado: {i+1}")
    conn.close()

if __name__ == "__main__":
    publish(10000)
