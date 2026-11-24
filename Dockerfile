# syntax=docker/dockerfile:1
# ターゲット: web (配信用) / updater (過去問の定期更新用)
#   docker build --target web     -t sikaku-web .
#   docker build --target updater -t sikaku-updater .

FROM python:3.12-slim-bookworm AS base
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
WORKDIR /app

# ---------- 配信用 ----------
FROM base AS web
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --only-group web
COPY main.py ./
COPY static ./static
RUN mkdir -p extractor/datas
VOLUME /app/extractor/datas
EXPOSE 11188
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "11188"]

# ---------- 更新用 ----------
FROM base AS updater
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --only-group updater
COPY extractor ./extractor
RUN chmod +x extractor/update_loop.sh
VOLUME /app/extractor/datas
CMD ["/app/extractor/update_loop.sh"]
