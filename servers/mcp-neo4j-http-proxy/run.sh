#!/bin/bash

# Neo4j MCP HTTP Proxy Startup Script

set -e

echo "🚀 Starting Neo4j MCP HTTP Proxy Server"
echo "========================================"

# Check if .env file exists
if [ -f .env ]; then
    echo "📄 Loading environment variables from .env file"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found, using defaults"
fi

# Set defaults if not provided
export NEO4J_URL=${NEO4J_URL:-"bolt://localhost:7687"}
export NEO4J_USERNAME=${NEO4J_USERNAME:-"neo4j"}
export NEO4J_PASSWORD=${NEO4J_PASSWORD:-"password"}
export NEO4J_DATABASE=${NEO4J_DATABASE:-"neo4j"}
export HTTP_HOST=${HTTP_HOST:-"0.0.0.0"}
export HTTP_PORT=${HTTP_PORT:-"69420"}
export HTTP_PATH=${HTTP_PATH:-"/mcp"}

echo "🔧 Configuration:"
echo "   Neo4j URL: $NEO4J_URL"
echo "   Neo4j User: $NEO4J_USERNAME"
echo "   Neo4j Database: $NEO4J_DATABASE"
echo "   HTTP Server: $HTTP_HOST:$HTTP_PORT$HTTP_PATH"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Setting up virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e .
else
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

echo "🎯 Starting server..."
echo "   Health check: http://$HTTP_HOST:$HTTP_PORT/health"
echo "   MCP endpoint: http://$HTTP_HOST:$HTTP_PORT$HTTP_PATH"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the server
mcp-neo4j-http-proxy \
    --db-url "$NEO4J_URL" \
    --username "$NEO4J_USERNAME" \
    --password "$NEO4J_PASSWORD" \
    --database "$NEO4J_DATABASE" \
    --host "$HTTP_HOST" \
    --port "$HTTP_PORT" \
    --path "$HTTP_PATH" 