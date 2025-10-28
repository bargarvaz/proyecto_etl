#!/usr/bin/env bash
set -euo pipefail
TS=$(date +"%Y%m%d_%H%M%S")
mkdir -p ~/proyecto_etl/backups
docker exec -i etl_postgres pg_dump -U pguser -d payments | gzip > ~/proyecto_etl/backups/payments_${TS}.sql.gz
echo "Backup en ~/proyecto_etl/backups/payments_${TS}.sql.gz"
