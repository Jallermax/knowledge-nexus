# Builder stage
FROM python:3.12-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache build-base

# Copy and install dependencies
COPY ./requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./graph_rag /app/graph_rag
COPY ./main.py /app/main.py
COPY ./config /app/config

# Final stage
FROM python:3.12-alpine AS final

LABEL maintainer="Jallermax <jallermax@gmail.com>"
LABEL version="0.0.1-alpha"
LABEL description="Ingest your knwoledge base into a graph database and query it with LLM"
LABEL license="GNU GPLv3"
LABEL source="https://github.com/Jallermax/knowledge-nexus"

WORKDIR /app

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code
COPY --from=builder /app /app

CMD ["python", "main.py"]
