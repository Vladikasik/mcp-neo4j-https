# Neo4j MCP SSE Bridge

Production-ready Server-Sent Events (SSE) bridge for Model Context Protocol (MCP) with Neo4j knowledge graph functionality, designed for deployment at memory.aynshteyn.dev/mcp.

## Features

- **Knowledge Graph Management**: Create, read, update, and delete entities and relationships
- **Memory Persistence**: Store conversation context and insights across sessions
- **Cypher Query Execution**: Direct Neo4j database access for advanced operations
- **SSE Connectivity**: Real-time communication with MCP clients over HTTPS
- **Production Security**: SSL/TLS encryption and secure authentication
- **Domain-Ready**: Pre-configured for memory.aynshteyn.dev deployment

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env` file

3. Run the server:
```bash
python main.py
```

## Production Deployment

The server is designed for deployment at **https://memory.aynshteyn.dev/mcp**

- **Development**: Runs on HTTP port 8000 without SSL
- **Production**: Runs on HTTPS port 443 with SSL certificates
- **Transport**: SSE (Server-Sent Events) for real-time communication
- **Path**: Serves MCP functionality on `/mcp` endpoint

### SSL Certificate Requirements

For production deployment with SSL, ensure the SSL certificate files exist at the paths specified in your `.env` file:
- `SSL_CERTFILE` must point to a valid SSL certificate file
- `SSL_KEYFILE` must point to the corresponding private key file

The server automatically detects SSL certificate availability and falls back to HTTP for development if certificates are not found.

## Core Functionality

### Entity Management
- Create and organize knowledge entities with types and observations
- Establish relationships between entities using active voice descriptions
- Search and retrieve entities by name, type, or content

### Knowledge Graph Operations
- Full graph reading and visualization
- Targeted entity searches and filtering
- Bulk operations for efficient data management

### Database Integration
- Direct Cypher query execution for advanced operations
- Secure Neo4j connection with authentication
- Support for both local and cloud Neo4j instances

## STDIO Servers

The `servers/` directory contains standalone MCP servers that operate over STDIO:

- **mcp-neo4j-memory**: Knowledge graph memory storage
- **mcp-neo4j-cypher**: Natural language to Cypher translation
- **mcp-neo4j-cloud-aura-api**: Neo4j Aura cloud management

These servers can be used independently with any MCP client that supports STDIO communication.

## License

MIT License