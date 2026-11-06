# One image for the whole site: FastAPI serves /api and the built React app.
# Build from the repo root: docker build -f deploy/Dockerfile .

# 1. Build the frontend
FROM node:24-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# 2. Python app; same layout as the repo so main.py finds ../frontend/dist
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/backend/.venv/bin:$PATH"
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock backend/.python-version ./
RUN uv sync --frozen --no-dev
COPY backend/app ./app
COPY --from=frontend /app/frontend/dist /app/frontend/dist

# Render sets PORT (10000 by default); 8000 when run locally
CMD ["sh", "-c", "exec fastapi run app/main.py --host 0.0.0.0 --port ${PORT:-8000}"]
