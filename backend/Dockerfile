FROM python:3.11-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements-runtime.txt .
RUN python -m pip wheel --wheel-dir /wheels -r requirements-runtime.txt

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=cs_career_guide.settings

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        ca-certificates \
        libmariadb3 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 appgroup \
    && useradd --system --uid 10001 --gid appgroup --create-home appuser

WORKDIR /app
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
    && rm -rf /wheels

COPY . /app
RUN mkdir -p /app/staticfiles /app/media /data/staticfiles /data/media /data/lancedb \
    && chmod +x /app/docker-entrypoint.sh \
    && chown -R appuser:appgroup /app/staticfiles /app/media /data

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD ["python", "-c", "import socket; s=socket.create_connection(('127.0.0.1',8000),3); s.close()"]

ENTRYPOINT ["/app/docker-entrypoint.sh"]
