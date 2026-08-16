FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt /app/api/requirements.txt
COPY detector/requirements.txt /app/detector/requirements.txt
RUN pip install --no-cache-dir -r /app/api/requirements.txt -r /app/detector/requirements.txt

COPY api /app/api
COPY detector /app/detector
COPY sumo_csv_export.py /app/sumo_csv_export.py

ENV PYTHONPATH=/app:/app/api:/app/detector

WORKDIR /app/api
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
