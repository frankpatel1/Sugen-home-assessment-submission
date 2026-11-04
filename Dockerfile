FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-packaged index and data
COPY data/enriched_mms.json /app/data/enriched_mms.json
COPY data/mms-2026-01.json /app/data/mms-2026-01.json

# Application source code
COPY src /app/src

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "-m", "src.main"]
