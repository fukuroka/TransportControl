FROM python:3.12-slim AS builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    git \
 && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /tmp/uv-install.sh
RUN chmod +x /tmp/uv-install.sh && /tmp/uv-install.sh && rm /tmp/uv-install.sh

ENV PATH="/root/.local/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml uv.lock ./

RUN uv venv .venv \
 && cp $(which uv) .venv/bin/ \
 && .venv/bin/uv sync --frozen --no-editable


FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/* \

COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

CMD ["python", "src/tg_bot.py"]
