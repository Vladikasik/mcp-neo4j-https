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
        import uvicorn
        
        # Check SSL availability and adjust configuration
        ssl_config = {}
        if settings.ssl_available():
            ssl_config = {
                "ssl_keyfile": settings.ssl_keyfile,
                "ssl_certfile": settings.ssl_certfile
            }
            logging.info(f"Starting server with SSL on {settings.http_host}:{settings.http_port}")
        else:
            # Fall back to HTTP for development
            if settings.http_port == 443:
                settings.http_port = 8000
            logging.info(f"SSL certificates not found, starting HTTP server on {settings.http_host}:{settings.http_port}")
            logging.warning("For production deployment, ensure SSL certificates are available at the specified paths")
        
        uvicorn.run(
            "main:mcp",
            host=settings.http_host,
            port=settings.http_port,
            access_log=True,
            log_level="info",
            **ssl_config
        )
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        sys.exit(1) 