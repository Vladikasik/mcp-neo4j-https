# Neo4j MCP HTTP Proxy

HTTP server for the Neo4j Memory MCP tool. Exposes Neo4j knowledge graph memory over HTTP using SSE transport, making it compatible with MCP Inspector, ChatGPT, and other HTTP-based MCP clients.

## Features

- **HTTP Access**: Neo4j memory functionality over HTTP using SSE transport
- **Complete Compatibility**: All original Neo4j memory tools preserved
- **Production Ready**: Built with FastMCP for reliability and performance
- **Easy Deployment**: Simple configuration and deployment

## Quick Start

### Installation

```bash
cd servers/mcp-neo4j-http-proxy
pip install -e .
```

### Configuration

Create `.env` file:
```bash
NEO4J_URL=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
HTTP_HOST=0.0.0.0
HTTP_PORT=8000
```

### Run Server

```bash
mcp-neo4j-http-proxy
```

Or use the startup script:
```bash
./run.sh
```

### Test

```bash
curl http://localhost:8000/health
python test_server.py
```

## Available Tools

- `create_entities` - Create multiple new entities
- `create_relations` - Create relationships between entities  
- `add_observations` - Add observations to existing entities
- `delete_entities` - Delete entities and relations
- `delete_observations` - Delete specific observations
- `delete_relations` - Delete relationships
- `read_graph` - Read the entire knowledge graph
- `search_nodes` - Search nodes by query
- `find_nodes` - Find nodes by name
- `open_nodes` - Open specific nodes

## MCP Client Connection

**URL**: `http://your-server:8000/sse`

Works with:
- MCP Inspector
- ChatGPT (with MCP support)
- Claude Desktop
- Any SSE-compatible MCP client

## Docker Deployment

```bash
docker build -t mcp-neo4j-http .
docker run -d -p 8000:8000 \
  -e NEO4J_URL=neo4j+s://your-instance.databases.neo4j.io \
  -e NEO4J_PASSWORD=your-password \
  mcp-neo4j-http
```

## Configuration Options

Environment variables or command line arguments:

- `NEO4J_URL` - Neo4j connection URL
- `NEO4J_USERNAME` - Neo4j username (default: neo4j)
- `NEO4J_PASSWORD` - Neo4j password
- `NEO4J_DATABASE` - Database name (default: neo4j)
- `HTTP_HOST` - Server host (default: 0.0.0.0)
- `HTTP_PORT` - Server port (default: 8000)

## Security

This server has no built-in authentication. For production:
- Use behind reverse proxy with authentication
- Configure firewall rules
- Consider VPN or network isolation

## License

MIT 