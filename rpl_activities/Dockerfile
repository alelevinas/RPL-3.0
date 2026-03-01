# Multi-stage Dockerfile for RPL-3.0 Activities Service
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY base_requirements.txt extra_requirements.txt ./
RUN pip install --user --no-cache-dir -r base_requirements.txt -r extra_requirements.txt

# Final stage
FROM python:3.13-slim

WORKDIR /

# Copy only installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy source code
COPY ./rpl_activities/src /rpl_activities/src
COPY ./rpl_activities/__init__.py /rpl_activities/__init__.py

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "rpl_activities.src.main:app", "--host", "0.0.0.0", "--port", "80", "--use-colors"]
