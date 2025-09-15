# Stage 1: build wheels cache (speeds up downstream builds)
FROM python:3.11-slim AS wheels
WORKDIR /w
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN pip install --upgrade pip build wheel
RUN pip wheel --wheel-dir /wheels .

# Stage 2: runtime
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    HF_HOME=/models MPLCONFIGDIR=/tmp/mpl
WORKDIR /app
COPY --from=wheels /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY src/ ./src/
RUN pip install --no-cache-dir -e .
ENTRYPOINT ["python","-m","controller.server"]
