# Use a lightweight Python + Node.js base
FROM nikolaik/python-nodejs:python3.11-nodejs20-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the project
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir requests

# Expose the proxy port
EXPOSE 11435

# Default environment variables
ENV OLLAMA_URL=http://host.docker.internal:11434/api/chat

# The entrypoint can be the proxy or the runtime
ENTRYPOINT ["node", "proxy.js"]
