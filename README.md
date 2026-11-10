# self-service (Superset 6.1.0)

Docker Compose deployment of Superset 6.1.0 with NASCOP login, embedding and reports.
It runs the web app, Celery worker, Celery beat, Redis and PostgreSQL.

Containers run as the non-root `superset` user and mount `./docker` read-only. Python packages are baked into the image from `docker/requirements-local.txt`, so run `docker compose build` after changing them.

## Setup

```sh
cp docker/.env-non-dev.example docker/.env-non-dev
cp docker/pythonpath_dev/client_secret.example.json docker/pythonpath_dev/client_secret.json
docker compose build
```

Fill in the blank values in `docker/.env-non-dev`, and `client_secret` in `client_secret.json`. The container user must be able to read `client_secret.json`.

## Login modes

Set `SUPERSET_AUTH_MODE` in `docker/.env-non-dev`:

- `oauth` (production): OpenID Connect against the identity provider in `client_secret.json`.
- `db` (local): Superset's own username and password login.

For `oauth`, register this callback URL with the identity provider:

```text
https://<your-domain>/oauth-authorized/kenyahmis
```

Create a local admin for `db` mode with:

```sh
docker compose run --rm superset superset fab create-admin
```

## Upgrading the metadata database

Stop the old stack and take a `pg_dump` first. The migrations change the schema, and going back means restoring that backup.

```sh
docker compose run --rm superset bash -c "superset db upgrade && superset init && python /app/docker/grant_6x_permissions.py"
docker compose up -d
```

`grant_6x_permissions.py` gives custom organization roles the read and drill permissions added in 6.x. New organization roles created later need these permissions too, so rerun it after adding roles.

`SUPERSET_SECRET_KEY` must match the key the database was last used with, or stored connection passwords cannot be decrypted. To rotate it, set `PREVIOUS_SECRET_KEY` to the old value and the new value in `SUPERSET_SECRET_KEY`, run the command below, then clear `PREVIOUS_SECRET_KEY`:

```sh
docker compose run --rm superset superset re-encrypt-secrets
```

## Backing up and restoring the database

Create a backup while the stack is running:

```sh
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > superset_$(date +%Y%m%d_%H%M).dump
```

Restore one with:

```sh
./restore-db.sh /path/to/backup.dump
```

The script accepts `pg_dump` custom-format files and plain `.sql` files. It **replaces the whole database in the `db` service**, then upgrades it to this Superset version, reapplies permissions and restarts the stack. It requires `DATABASE_HOST=db`. `SUPERSET_SECRET_KEY` must be the key in use when the backup was taken.

## Network

The app is published on `127.0.0.1:8088` by default. Set `SUPERSET_PUBLISH` to change it, and put a TLS reverse proxy in front.
