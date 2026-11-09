FROM apache/superset:6.1.0

USER root
COPY docker/requirements-local.txt /tmp/requirements-local.txt
RUN uv pip install --python /app/.venv/bin/python --no-cache -r /tmp/requirements-local.txt \
    && rm /tmp/requirements-local.txt
USER superset
