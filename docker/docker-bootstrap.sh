#!/usr/bin/env bash
set -eo pipefail

case "${1}" in
  worker)
    echo "Starting Celery worker..."
    exec celery --app=superset.tasks.celery_app:app worker -O fair -l INFO
    ;;
  beat)
    echo "Starting Celery beat..."
    rm -f /tmp/celerybeat.pid
    exec celery --app=superset.tasks.celery_app:app beat --pidfile /tmp/celerybeat.pid -l INFO -s "${SUPERSET_HOME}"/celerybeat-schedule
    ;;
  app-gunicorn)
    echo "Starting web app..."
    exec /usr/bin/run-server.sh
    ;;
  *)
    echo "Unknown operation: ${1}" >&2
    exit 1
    ;;
esac
