FROM node:22-bookworm-slim AS web
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ENV PUBLIC_API_URL=""
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app:/app/backend STATIC_DIR=/app/site RAG_ENABLED=false
COPY backend/requirements.txt backend/requirements.txt
COPY analytics/requirements.txt analytics/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt -r analytics/requirements.txt
COPY backend backend
COPY shared shared
COPY analytics analytics
COPY --from=web /app/dist /app/site
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
