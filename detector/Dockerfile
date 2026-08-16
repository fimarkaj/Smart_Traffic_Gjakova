FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y python3 python3-pip libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY detector/requirements.txt /app/detector/requirements.txt
COPY api/requirements.txt /app/api/requirements.txt
RUN pip3 install --no-cache-dir -r /app/detector/requirements.txt -r /app/api/requirements.txt

COPY detector /app/detector
COPY api /app/api

ENV PYTHONPATH=/app:/app/detector:/app/api

WORKDIR /app/detector
CMD ["python3", "detector.py"]
