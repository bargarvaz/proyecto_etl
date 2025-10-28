# Prueba Técnica — DBA + ETL (RabbitMQ)

## Ejecución
1) cd compose && docker compose up -d
2) ../scripts/bootstrap.sh
3) python3 ./scripts/publish.py

Observabilidad:
- Prometheus: http://localhost:9090 (alerta PostgresDown)
- Grafana: http://localhost:3000 (admin/admin) → Dashboard "ETL Overview"
Backups: ./scripts/backup.sh (restaurar a payments_restore con el último .sql.gz)
