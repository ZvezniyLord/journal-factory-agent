FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends antiword \
    && rm -rf /var/lib/apt/lists/*
# Install project requirements and necessary libraries for Gemma 4 2B
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install transformers torch accelerate
COPY . .

EXPOSE 8765
CMD ["python", "-m", "journal_factory.cli", "serve", "--host", "0.0.0.0", "--port", "8765"]
