# -------- Stage 1: build wheels (needs pyproject.toml + src/) --------
FROM python:3.11-slim AS wheels
WORKDIR /w

# Build tools
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata and source (both are required to build a wheel)
COPY pyproject.toml ./
COPY src/ ./src/

RUN python -m pip install --upgrade pip build wheel
# Build a wheel for our package into /wheels
RUN python -m build --wheel --outdir /wheels .

# -------- Stage 2: runtime (install the prebuilt wheel) --------
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    HF_HOME=/models MPLCONFIGDIR=/tmp/mpl
WORKDIR /app

# Install from the wheel (fast, no compilers needed)
COPY --from=wheels /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy source too so editable dev tools (like hud analyze) can show line numbers,
# but runtime uses the installed wheel.
COPY src/ ./src/

# Default entrypoint runs the MCP server over stdio
ENTRYPOINT ["python","-m","controller.server"]
