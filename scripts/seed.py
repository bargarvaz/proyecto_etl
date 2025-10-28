import argparse, csv, os, random, uuid
from datetime import datetime, timedelta
from faker import Faker
fake = Faker("es_MX")

def iso(dt): return dt.strftime("%Y-%m-%d %H:%M:%S")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--accounts", type=int, default=50000)
    p.add_argument("--merchants", type=int, default=5000)
    p.add_argument("--terminals", type=int, default=10000)
    p.add_argument("--txns", type=int, default=1000000)
    p.add_argument("--chunk", type=int, default=100000)
    p.add_argument("--out", type=str, default="data")
    p.add_argument("--start", type=str, default="2024-01-01")
    p.add_argument("--end", type=str, default="2025-10-01")
    args = p.parse_args()

    outdir = os.path.abspath(args.out)
    os.makedirs(outdir, exist_ok=True)

    start = datetime.fromisoformat(args.start)
    end   = datetime.fromisoformat(args.end)
    span_seconds = int((end - start).total_seconds())

    # 1) Accounts
    accounts = [str(uuid.uuid4()) for _ in range(args.accounts)]
    with open(os.path.join(outdir, "accounts.csv"), "w", newline="") as f:
        w = csv.writer(f)
        now = datetime.utcnow()
        for aid in accounts:
            w.writerow([aid, fake.name(), iso(now)])

    # 2) Merchants
    merchants = [str(uuid.uuid4()) for _ in range(args.merchants)]
    with open(os.path.join(outdir, "merchants.csv"), "w", newline="") as f:
        w = csv.writer(f)
        for mid in merchants:
            w.writerow([mid, fake.company()])

    # 3) Terminals (cada terminal pertenece a un merchant)
    terminals = []
    with open(os.path.join(outdir, "terminals.csv"), "w", newline="") as f:
        w = csv.writer(f)
        for _ in range(args.terminals):
            tid = str(uuid.uuid4())
            mid = random.choice(merchants)
            terminals.append((tid, mid))
            w.writerow([tid, mid, fake.city()])

    # 4) TXNs en chunks: (account_id, merchant_id, terminal_id, amount, currency, status, created_at)
    def rand_dt():
        return start + timedelta(seconds=random.randint(0, span_seconds))

    statuses = ["ok", "reversed", "declined"]
    n = args.txns
    chunk = args.chunk
    files = (n + chunk - 1)//chunk
    for i in range(files):
        lo = i*chunk
        hi = min((i+1)*chunk, n)
        path = os.path.join(outdir, f"txn_{i:02d}.csv")
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            for _ in range(lo, hi):
                acc = random.choice(accounts)
                term_id, merch_id = random.choice(terminals)
                amount = round(random.uniform(1, 2000), 2)
                curr = "MXN"
                st = random.choices(statuses, weights=[92,5,3], k=1)[0]
                ts = rand_dt()
                w.writerow([acc, merch_id, term_id, amount, curr, st, iso(ts)])

    print("OK: CSVs generados en", outdir)

if __name__ == "__main__":
    main()
