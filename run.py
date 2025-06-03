#!/usr/bin/env python3

import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    try:
        from main import mcp, settings
        
        # Check SSL availability and determine transport configuration
        if settings.ssl_available():
            logging.info(f"Starting Neo4j MCP Bridge with SSL on https://{settings.http_host}:{settings.http_port}{settings.http_path}")
            mcp.run(
                transport="sse", 
                host=settings.http_host,
                port=settings.http_port,
                path=settings.http_path,
                ssl_keyfile=settings.ssl_keyfile,
                ssl_certfile=settings.ssl_certfile
            )
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