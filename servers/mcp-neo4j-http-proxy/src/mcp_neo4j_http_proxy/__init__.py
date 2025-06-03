import asyncio
import argparse
import os
from .server import create_http_proxy


def main():
    """Main entry point for the HTTP proxy server."""
    parser = argparse.ArgumentParser(description='Neo4j Memory MCP HTTP Proxy Server')
    
    # Neo4j connection arguments
    parser.add_argument('--db-url', 
                       default=os.getenv("NEO4J_URL", "bolt://localhost:7687"),
                       help='Neo4j connection URL')
    parser.add_argument('--username', 
                       default=os.getenv("NEO4J_USERNAME", "neo4j"),
                       help='Neo4j username')
    parser.add_argument('--password', 
                       default=os.getenv("NEO4J_PASSWORD", "password"),
                       help='Neo4j password')
    parser.add_argument("--database",
                        default=os.getenv("NEO4J_DATABASE", "neo4j"),
                        help="Neo4j database name")
    
    # HTTP server arguments  
    parser.add_argument('--host',
                       default=os.getenv("HTTP_HOST", "0.0.0.0"),
                       help='HTTP server host')
    parser.add_argument('--port',
                       type=int,
                       default=int(os.getenv("HTTP_PORT", "8000")),
                       help='HTTP server port')
    parser.add_argument('--path',
                       default=os.getenv("HTTP_PATH", "/mcp"),
                       help='HTTP endpoint path')
    
    # SSL/HTTPS arguments
    parser.add_argument('--ssl-certfile',
                       default=os.getenv("SSL_CERTFILE"),
                       help='Path to SSL certificate file (.pem)')
    parser.add_argument('--ssl-keyfile',
                       default=os.getenv("SSL_KEYFILE"),
                       help='Path to SSL private key file (.pem)')
    parser.add_argument('--ssl',
                       action='store_true',
                       default=os.getenv("SSL_ENABLED", "").lower() in ("true", "1", "yes"),
                       help='Enable SSL/HTTPS')
    
    args = parser.parse_args()
    
    # Run the HTTP proxy server
    asyncio.run(create_http_proxy(
        neo4j_url=args.db_url,
        neo4j_username=args.username,
        neo4j_password=args.password,
        neo4j_database=args.database,
        host=args.host,
        port=args.port,
        path=args.path,
        ssl_certfile=args.ssl_certfile,
        ssl_keyfile=args.ssl_keyfile,
        ssl_enabled=args.ssl
    ))


__all__ = ["main"] 