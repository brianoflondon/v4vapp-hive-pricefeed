FROM python:3.11

RUN python -m pip install --no-cache-dir uv

# Copy pyproject and lockfile if present
COPY ./pyproject.toml ./uv.lock* /app/

WORKDIR /app/

RUN UV_PROJECT_ENVIRONMENT=/usr/local uv sync --locked --no-install-project

COPY ./src /app/

CMD [ "python", "v4vapp_hive_pricefeed/pricefeed.py"]
