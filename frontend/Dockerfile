FROM node:24-bookworm-slim AS builder

WORKDIR /build/frontend
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --prefer-offline --no-audit --no-fund
COPY . ./
ARG VITE_API_BASE_URL=/api
ARG VITE_COMPANY_API_BASE_URL=/company-api
ARG VITE_ENABLE_TTS=False
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_COMPANY_API_BASE_URL=${VITE_COMPANY_API_BASE_URL} \
    VITE_ENABLE_TTS=${VITE_ENABLE_TTS}
RUN npm run build && rm -rf dist/models

FROM nginx:1.27-alpine

# Stable public models have their own layer, independent of the Vue build.
# Keep this before frequently changing config/application files.
COPY public/models /usr/share/nginx/html/models
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /build/frontend/dist /usr/share/nginx/html
RUN mkdir -p /var/cache/nginx \
    && sed -i \
        -e '/^user /d' \
        -e 's#^[[:space:]]*pid[[:space:]][^;]*;#pid /tmp/nginx.pid;#' \
        -e 's/worker_processes[[:space:]]*auto;/worker_processes 1;/' \
        /etc/nginx/nginx.conf \
    && grep -Eq '^pid[[:space:]]+/tmp/nginx.pid;' /etc/nginx/nginx.conf \
    && chown -R 10001:10001 /var/cache/nginx

USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["wget", "-q", "--spider", "http://127.0.0.1:8080/"]
