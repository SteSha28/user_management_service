FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*


RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libpq-dev \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /app
COPY . .

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
