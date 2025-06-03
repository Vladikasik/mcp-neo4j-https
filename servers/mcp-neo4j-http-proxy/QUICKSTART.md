# 🚀 Quick Start Guide

Get your Neo4j MCP HTTP server running in 5 minutes.

## Prerequisites

- Python 3.10+
- Neo4j running (local or Aura Cloud)

## 1. Install

```bash
cd servers/mcp-neo4j-http-proxy
pip install -e .
```

## 2. Configure

```bash
cp config.example .env
# Edit .env with your Neo4j credentials
```

## 3. Run

```bash
mcp-neo4j-http-proxy
```

## 4. Test

```bash
curl http://localhost:8000/health
```

## 5. Connect MCP Client

**URL**: `http://localhost:8000/sse`

## Done! 🎉

Your Neo4j knowledge graph is now accessible over HTTP. 