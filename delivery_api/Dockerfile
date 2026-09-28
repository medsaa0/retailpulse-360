FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY . .

EXPOSE 8002

CMD ["uv", "run", "uvicorn", "delivery_api.main:app", "--host", "0.0.0.0", "--port", "8002"]
