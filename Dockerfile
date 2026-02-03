FROM python:3.11-slim

WORKDIR /app

# System deps for spaCy
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml .
RUN pip install --no-cache-dir . && \
    python -m spacy download en_core_web_lg

# App code
COPY tools/ tools/
COPY server/ server/

ENV OLLAMA_URL=http://172.17.0.1:11434

EXPOSE 8000

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
