FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash mcp
USER mcp

# Expose the default port
EXPOSE 69420

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:69420/health || exit 1

# Set default environment variables
ENV NEO4J_URL=bolt://localhost:7687
ENV NEO4J_USERNAME=neo4j
ENV NEO4J_PASSWORD=password
ENV NEO4J_DATABASE=neo4j
ENV HTTP_HOST=0.0.0.0
ENV HTTP_PORT=69420
ENV HTTP_PATH=/mcp

# Run the server
CMD ["mcp-neo4j-http-proxy"] 