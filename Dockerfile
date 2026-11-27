FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Dependencies first, so a code change doesn't reinstall them
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY gloomraven ./gloomraven
RUN uv sync --locked --no-dev

# phue keeps the Hue bridge username in $HOME/.python_hue, so HOME is the persistent data volume
RUN useradd --system --home-dir /data --create-home gloomraven
USER gloomraven
ENV HOME=/data
VOLUME /data

ENTRYPOINT ["python", "-m", "gloomraven.main"]
