#!/usr/bin/env bash
# Replace the database in the db service with a backup, then upgrade and restart.
# Usage: ./restore-db.sh <backup.dump|backup.sql>
set -euo pipefail

cd "$(dirname "$0")"

backup="${1:-}"
if [ -z "$backup" ] || [ ! -f "$backup" ]; then
  echo "Usage: $0 <backup.dump|backup.sql>" >&2
  exit 1
fi

if ! grep -qx 'DATABASE_HOST=db' docker/.env-non-dev; then
  echo "Refusing to restore: DATABASE_HOST in docker/.env-non-dev is not 'db'." >&2
  exit 1
fi

if [ "$(head -c 5 "$backup")" = "PGDMP" ]; then
  format=custom
else
  format=plain
fi

echo "This replaces ALL data in the db service with: $backup ($format format)"
read -r -p "Type 'restore' to continue: " answer
if [ "$answer" != "restore" ]; then
  echo "Cancelled."
  exit 1
fi

docker compose stop superset superset-worker superset-worker-beat
docker compose up -d --wait db redis

docker compose exec -T db sh -c '
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres \
    -c "DROP DATABASE IF EXISTS \"$POSTGRES_DB\" WITH (FORCE)" \
    -c "CREATE DATABASE \"$POSTGRES_DB\" OWNER \"$POSTGRES_USER\""
'

if [ "$format" = "custom" ]; then
  docker compose exec -T db sh -c '
    pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges --exit-on-error
  ' < "$backup"
else
  # Plain dumps may name roles that do not exist here, so errors are shown rather than fatal.
  docker compose exec -T db sh -c 'psql -q -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < "$backup"
fi

# Redis only holds caches and task queues, which would be stale after a restore.
docker compose exec -T redis redis-cli FLUSHALL

docker compose run --rm -T superset bash -c \
  "superset db upgrade && superset init && python /app/docker/grant_6x_permissions.py"

docker compose up -d
echo "Restore complete."
