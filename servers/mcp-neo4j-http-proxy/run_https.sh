#!/bin/bash

# Production HTTPS startup script for memory.aynshteyn.dev
# Run with: ./run_https.sh

set -e

echo "🚀 Starting Neo4j MCP HTTP Proxy with HTTPS..."

# Check if SSL certificates exist
CERT_PATH="${SSL_CERTFILE:-/home/user/ssl/domain.cert.pem}"
KEY_PATH="${SSL_KEYFILE:-/home/user/ssl/private.key.pem}"

if [ ! -f "$CERT_PATH" ]; then
    echo "❌ SSL certificate not found at: $CERT_PATH"
    echo "Please copy your domain.cert.pem file to this location"
    exit 1
fi

if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSL private key not found at: $KEY_PATH"
    echo "Please copy your private.key.pem file to this location"
    exit 1
fi

echo "✅ SSL certificates found"
echo "📜 Certificate: $CERT_PATH"
echo "🔐 Private key: $KEY_PATH"

# Export environment variables from production config
if [ -f ".env" ]; then
    echo "📋 Loading production configuration..."
    export $(grep -v '^#' .env | xargs)
fi

# Start the server with HTTPS
echo "🌐 Starting server on https://memory.aynshteyn.dev (port 443)..."

python -m mcp_neo4j_http_proxy \
    --ssl \
    --ssl-certfile "$CERT_PATH" \
    --ssl-keyfile "$KEY_PATH" \
    --port 443 \
    --host 0.0.0.0

echo "🎉 Server started successfully!" 