Repo: https://github.com/bargarvaz/proyecto_etl

Cómo ejecutar:
  cd compose && docker compose up -d
  ../scripts/bootstrap.sh
  python3 ./scripts/publish.py

Verificación rápida:
  payments.txn crece y etl.txn_daily_agg tiene datos
  Prometheus (http://localhost:9090) con alerta PostgresDown
  Grafana (http://localhost:3000, admin/admin) → dashboard ETL Overview
  Backups:
    ./scripts/backup.sh (restore a payments_restore con el último .sql.gz)

Notas:
  Incluye planes EXPLAIN en docs/plans/
  .env.example con variables; .env está ignorado

------

Prueba Técnica — DBA & ETL

Este proyecto implementa un pipeline ETL con infraestructura Docker, monitoreo en tiempo real y respaldo automatizado.
Integra PostgreSQL, RabbitMQ, Prometheus, Grafana y un worker ETL en Python que procesa datos transaccionales simulados.

---

Arquitectura
- PostgreSQL 15 — Base principal con esquema `payments` y `etl`
  - Tablas particionadas (txn_YYYYMM) optimizadas por rango temporal
  - Scripts `init/` y `migrations/` para inicialización y limpieza
- RabbitMQ — Canal de mensajería (`txn_etl`) con DLQ (`txn_etl.dlq`)
- ETL Worker (Python) — Consume mensajes y ejecuta transformaciones:
  - `stage → clean → aggregate`
  - Inserta resultados en `etl.txn_daily_agg`
- Prometheus + Exporter — Métricas de PostgreSQL
- Grafana — Dashboard “ETL Overview” y datasource autoprovisionado
- Alertas — Regla `PostgresDown` activa si la DB no reporta métricas

---

Estructura del Proyecto
compose/                 → Infraestructura Docker (docker-compose.yml)
db/init/                 → Creación de esquema, tablas y particiones
db/migrations/           → Limpieza y agregaciones ETL
scripts/                 → Python y Bash (publish, backup, bootstrap)
prometheus/rules/        → Reglas de alerta
grafana/provisioning/    → Datasource + Dashboard autoprovisionados
docs/                    → Evidencias, README y planes de ejecución
backups/                 → Respaldos (.sql.gz)
.env.example             → Variables de entorno

---

Ejecución Rápida

Levantar la infraestructura
bash
cd compose
docker compose up -d

Inicializar tablas y verificaciones
bash
../scripts/bootstrap.sh

Publicar datos al ETL
bash
python3 ./scripts/publish.py

Validar pipeline
bash
docker exec -it etl_postgres psql -U pguser -d payments -c "SELECT count(*) FROM payments.txn;"
docker exec -it etl_postgres psql -U pguser -d payments -c "SELECT * FROM etl.txn_daily_agg ORDER BY day DESC LIMIT 10;"

---

Observabilidad

Prometheus: [http://localhost:9090](http://localhost:9090)
  Alerta `PostgresDown` si el exporter no reporta métricas por 1 min.
  Grafana: [http://localhost:3000](http://localhost:3000)

  Usuario: `admin` / `admin`
  Dashboard: ETL Overview (TPS, conexiones, buffers)

---

Backups y Restore
bash
./scripts/backup.sh

Restaurar a nueva base
bash
LATEST=$(ls -1t ./backups/*.sql.gz | head -1)
gunzip -c "$LATEST" | docker exec -i etl_postgres psql -U pguser -d payments_restore

Planes de ejecución
Evidencias guardadas en `docs/plans/`:
`txn_count_total.plan`
`txn_count_by_month.plan`
`txn_by_account_last90.plan`
`top_merchants_30d.plan`
`daily_agg_recent.plan`

---

Variables de entorno:
  POSTGRES_USER=pguser
  POSTGRES_PASSWORD=pgpass
  POSTGRES_DB=payments
  RABBITMQ_DEFAULT_USER=guest
  RABBITMQ_DEFAULT_PASS=guest

Mantenimiento
  Scripts de administración:
    `bootstrap.sh` — despliegue rápido
    `backup.sh` — respaldo comprimido
    Monitoreo: Prometheus + Grafana autoprovisionados
    Logs persistentes en volúmenes Docker
    `.env` protegido mediante `.gitignore`

---

Barush Garduño
📧 bargarvaz@gmail.com
💼 Proyecto técnico: DBA & ETL con RabbitMQ, PostgreSQL

---
