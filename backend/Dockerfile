# Backend image for local Compose and future server deploy.
#
# Environment contract:
# - Do NOT copy .env into the image (.dockerignore blocks it on purpose).
# - Runtime config must come from the orchestrator (Compose `environment:`,
#   Kubernetes secrets, platform env vars, etc.).
# - Local dev may use repo-root `.env` for Compose interpolation only; that file
#   is not baked into this image.
# - Variable names use the AI_LAB_* prefix (see backend/app/settings.py).

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY backend ./backend

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -e .

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=5s --retries=10 --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read()" || exit 1

CMD ["python", "-m", "uvicorn", "backend.app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
