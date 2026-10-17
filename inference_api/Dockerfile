FROM node:24-bookworm-slim AS frontend
WORKDIR /build
COPY inference_api/frontend/package.json inference_api/frontend/package-lock.json inference_api/frontend/.npmrc ./
RUN npm ci --ignore-scripts
COPY inference_api/frontend/index.html inference_api/frontend/tsconfig.json inference_api/frontend/tsconfig.app.json inference_api/frontend/tsconfig.node.json inference_api/frontend/vite.config.ts ./
COPY inference_api/frontend/eslint.config.js ./
COPY inference_api/frontend/scripts ./scripts
COPY inference_api/frontend/src ./src
RUN npm run build

FROM python:3.11-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 INFERENCE_RUNTIME_MODE=docker
WORKDIR /app
COPY inference_api/requirements.txt /app/inference_api/requirements.txt
RUN pip install --no-cache-dir -r /app/inference_api/requirements.txt \
    && groupadd --system inference && useradd --system --gid inference --home /app inference
COPY inference_api/run.py /app/inference_api/run.py
COPY inference_api/src /app/inference_api/src
COPY BancoModeloUse/dw/fixed_queries.py /app/BancoModeloUse/dw/fixed_queries.py
COPY model_evaluation/export.py /app/model_evaluation/export.py
COPY model_evaluation/schemas/evidence_packet.schema.json /app/model_evaluation/schemas/evidence_packet.schema.json
COPY inference_api/private/bi_snapshot.json /app/inference_api/private/bi_snapshot.json
COPY runpod/serving/manifest.json /app/runpod/serving/manifest.json
COPY --from=frontend /build/dist /app/inference_api/frontend/dist
USER inference
EXPOSE 8765
HEALTHCHECK --interval=20s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=3)" || exit 1
CMD ["python", "/app/inference_api/run.py", "serve"]
