import asyncio
import os
from typing import Dict, Any, Optional
from pathlib import Path

from fastmcp import FastMCP
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import uvicorn

load_dotenv()

class Settings(BaseSettings):
    http_port: int = 443
    neo4j_url: str
    neo4j_username: str = "neo4j"
    neo4j_password: str
    neo4j_database: str = "neo4j"
    http_host: str = "0.0.0.0"
    http_path: str = "/mcp"
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None

    def ssl_available(self) -> bool:
        """Check if SSL certificates are available and valid"""
        if not self.ssl_certfile or not self.ssl_keyfile:
            return False
        return Path(self.ssl_certfile).exists() and Path(self.ssl_keyfile).exists()

settings = Settings()

# Configure FastMCP for SSE transport on /mcp path
mcp = FastMCP("Neo4j MCP Bridge")

@mcp.tool()
def create_entities(entities: list[dict]) -> str:
    """Create multiple new entities in the knowledge graph"""
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver(
        settings.neo4j_url,
        auth=(settings.neo4j_username, settings.neo4j_password),
        database=settings.neo4j_database
    )
    
    with driver.session() as session:
        for entity in entities:
            name = entity.get("name")
            entity_type = entity.get("type")
            observations = entity.get("observations", [])
            
            session.run(
                """
                MERGE (e:Entity {name: $name, type: $type})
                WITH e
                UNWIND $observations AS obs
                MERGE (e)-[:HAS_OBSERVATION]->(o:Observation {content: obs})
                """,
                name=name, type=entity_type, observations=observations
            )
    
    driver.close()
    return f"Created {len(entities)} entities successfully"

@mcp.tool()
def create_relations(relations: list[dict]) -> str:
    """Create multiple new relations between entities in the knowledge graph"""
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver(
        settings.neo4j_url,
        auth=(settings.neo4j_username, settings.neo4j_password),
        database=settings.neo4j_database
    )
    
    with driver.session() as session:
        for relation in relations:
            source = relation.get("source")
            target = relation.get("target")
            relation_type = relation.get("relationType")
            
            session.run(
                f"""
                MATCH (a:Entity {{name: $source}})
                MATCH (b:Entity {{name: $target}})
                MERGE (a)-[r:{relation_type}]->(b)
                """,
                source=source, target=target
            )
    
    driver.close()
    return f"Created {len(relations)} relations successfully"

@mcp.tool()
def add_observations(observations: list[dict]) -> str:
    """Add new observations to existing entities in the knowledge graph"""
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver(
        settings.neo4j_url,
        auth=(settings.neo4j_username, settings.neo4j_password),
        database=settings.neo4j_database
    )
    
    with driver.session() as session:
        for obs in observations:
            entity_name = obs.get("entityName")
            contents = obs.get("contents", [])
            
            for content in contents:
                session.run(
                    """
                    MATCH (e:Entity {name: $entity_name})
                    MERGE (e)-[:HAS_OBSERVATION]->(o:Observation {content: $content})
                    """,
                    entity_name=entity_name, content=content
                )
    
    driver.close()
    return f"Added observations to {len(observations)} entities successfully"

@mcp.tool()
def delete_entities(entityNames: list[str]) -> str:
    """Delete multiple entities and their associated relations from the knowledge graph"""
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver(
        settings.neo4j_url,
        auth=(settings.neo4j_username, settings.neo4j_password),
        database=settings.neo4j_database
    )
    
    with driver.session() as session:
        for entity_name in entityNames:
            session.run(
                """
                MATCH (e:Entity {name: $entity_name})
                DETACH DELETE e
                """,
                entity_name=entity_name
            )
    
    driver.close()
    return f"Deleted {len(entityNames)} entities successfully"

@mcp.tool()
def delete_observations(deletions: list[dict]) -> str:
    """Delete specific observations from entities in the knowledge graph"""
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver(
        settings.neo4j_url,
        auth=(settings.neo4j_username, settings.neo4j_password),
        database=settings.neo4j_database
    )
    
    with driver.session() as session:
        for deletion in deletions:
            entity_name = deletion.get("entityName")
            observations = deletion.get("observations", [])
            
            for obs in observations:
                session.run(
                    """
                    MATCH (e:Entity {name: $entity_name})-[:HAS_OBSERVATION]->(o:Observation {content: $obs})
                    DELETE o
                    """,
                    entity_name=entity_name, obs=obs
                )
    
    driver.close()
    return f"Deleted observations from {len(deletions)} entities successfully"

@mcp.tool()
def delete_relations(relations: list[dict]) -> str:
    """Delete multiple relations from the knowledge graph"""
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver(
        settings.neo4j_url,
        auth=(settings.neo4j_username, settings.neo4j_password),
        database=settings.neo4j_database
    )
    
    with driver.session() as session:
        for relation in relations:
            source = relation.get("source")
            target = relation.get("target")
            relation_type = relation.get("relationType")
            
            session.run(
                f"""
                MATCH (a:Entity {{name: $source}})-[r:{relation_type}]->(b:Entity {{name: $target}})
                DELETE r
                """,
                source=source, target=target
            )
    
    driver.close()
    return f"Deleted {len(relations)} relations successfully"

@mcp.tool()
def read_graph(random_string: str = "") -> str:
    """Read the entire knowledge graph"""
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver(
        settings.neo4j_url,
        auth=(settings.neo4j_username, settings.neo4j_password),
        database=settings.neo4j_database
    )
    
    with driver.session() as session:
        result = session.run(
            """
            MATCH (e:Entity)
            OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
            OPTIONAL MATCH (e)-[r]->(e2:Entity)
            RETURN e.name AS entity, e.type AS type, 
                   collect(DISTINCT o.content) AS observations,
                   collect(DISTINCT {type: type(r), target: e2.name}) AS relations
            """
        )
        
        entities = []
        for record in result:
            entities.append({
                "name": record["entity"],
                "type": record["type"],
                "observations": record["observations"],
                "relations": record["relations"]
            })
    
    driver.close()
    return f"Knowledge graph contains {len(entities)} entities: {entities}"

@mcp.tool()
def search_nodes(query: str) -> str:
    """Search for nodes in the knowledge graph based on a query"""
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver(
        settings.neo4j_url,
        auth=(settings.neo4j_username, settings.neo4j_password),
        database=settings.neo4j_database
    )
    
    with driver.session() as session:
        result = session.run(
            """
            MATCH (e:Entity)
            WHERE e.name CONTAINS $query OR e.type CONTAINS $query
            OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
            WHERE o.content CONTAINS $query
            RETURN DISTINCT e.name AS entity, e.type AS type
            """,
            query=query
        )
        
        entities = [{"name": record["entity"], "type": record["type"]} for record in result]
    
    driver.close()
    return f"Found {len(entities)} matching entities: {entities}"

@mcp.tool()
def find_nodes(names: list[str]) -> str:
    """Find specific nodes in the knowledge graph by their names"""
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver(
        settings.neo4j_url,
        auth=(settings.neo4j_username, settings.neo4j_password),
        database=settings.neo4j_database
    )
    
    with driver.session() as session:
        result = session.run(
            """
            MATCH (e:Entity)
            WHERE e.name IN $names
            OPTIONAL MATCH (e)-[:HAS_OBSERVATION]->(o:Observation)
            RETURN e.name AS entity, e.type AS type, collect(o.content) AS observations
            """,
            names=names
        )
        
        entities = []
        for record in result:
            entities.append({
                "name": record["entity"],
                "type": record["type"],
                "observations": record["observations"]
            })
    
    driver.close()
    return f"Found {len(entities)} entities: {entities}"

@mcp.tool()
def open_nodes(names: list[str]) -> str:
    """Open specific nodes in the knowledge graph by their names"""
    return find_nodes(names)

@mcp.tool()
def execute_cypher(query: str) -> str:
    """Execute a Cypher query against the Neo4j database"""
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver(
        settings.neo4j_url,
        auth=(settings.neo4j_username, settings.neo4j_password),
        database=settings.neo4j_database
    )
    
    with driver.session() as session:
        result = session.run(query)
        records = [record.data() for record in result]
    
    driver.close()
    return f"Query executed successfully. Results: {records}"

async def run_server_with_ssl():
    """Run FastMCP server with SSL using custom uvicorn configuration"""
    from fastapi import FastAPI
    from starlette.routing import Mount
    
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
        access_log=False
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    # Check SSL availability and determine configuration
    if settings.ssl_available():
        print(f"Starting Neo4j MCP Bridge with SSL on https://{settings.http_host}:{settings.http_port}{settings.http_path}")
        
        # Use modern streamable-http transport with SSL
        import ssl
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(settings.ssl_certfile, settings.ssl_keyfile)
        
        mcp.run(
            transport="streamable-http",
            host=settings.http_host,
            port=settings.http_port,
            path=settings.http_path,
            ssl_context=ssl_context
        )
    else:
        # Fall back to HTTP for development
        if settings.http_port == 443:
            settings.http_port = 8000
        print(f"SSL certificates not found, starting HTTP server on http://{settings.http_host}:{settings.http_port}{settings.http_path}")
        print("For production deployment, ensure SSL certificates are available at the specified paths")
        mcp.run(
            transport="sse",
            host=settings.http_host, 
            port=settings.http_port,
            path=settings.http_path
        ) 