#!/usr/bin/env python3

import sys
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def run_server_with_ssl(mcp, settings):
    """Run FastMCP server with SSL using custom uvicorn configuration"""
    from fastapi import FastAPI
    
    # Get the FastMCP SSE app
    mcp_app = mcp.sse_app()
    
    # Create a main FastAPI app to mount the MCP app on the correct path
    app = FastAPI()
    app.mount(settings.http_path, mcp_app)
    
    # Configure uvicorn with SSL
    config = uvicorn.Config(
        app,
        host=settings.http_host,
        port=settings.http_port,
        ssl_keyfile=settings.ssl_keyfile,
        ssl_certfile=settings.ssl_certfile,
        access_log=True,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        from main import mcp, settings
        
        # Check SSL availability and determine transport configuration
        if settings.ssl_available():
            logging.info(f"Starting Neo4j MCP Bridge with SSL on https://{settings.http_host}:{settings.http_port}{settings.http_path}")
            asyncio.run(run_server_with_ssl(mcp, settings))
        else:
            # Fall back to HTTP for development
            if settings.http_port == 443:
                settings.http_port = 8000
            logging.info(f"SSL certificates not found, starting HTTP server on http://{settings.http_host}:{settings.http_port}{settings.http_path}")
            logging.warning("For production deployment, ensure SSL certificates are available at the specified paths")
            mcp.run(
                transport="sse",
                host=settings.http_host, 
                port=settings.http_port,
                path=settings.http_path
            )
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        sys.exit(1) 