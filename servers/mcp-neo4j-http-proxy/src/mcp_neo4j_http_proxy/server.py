import json
import logging
from typing import Any, Dict, List

import neo4j
from neo4j import GraphDatabase
from pydantic import BaseModel
from fastmcp import FastMCP

# Set up logging
logger = logging.getLogger('mcp_neo4j_http_proxy')
logger.setLevel(logging.INFO)

# Models for our knowledge graph
class Entity(BaseModel):
    name: str
    type: str
    observations: List[str]

class Relation(BaseModel):
    source: str
    target: str
    relationType: str

class KnowledgeGraph(BaseModel):
    entities: List[Entity]
    relations: List[Relation]

class ObservationAddition(BaseModel):
    entityName: str
    contents: List[str]

class ObservationDeletion(BaseModel):
    entityName: str
    observations: List[str]

class Neo4jMemory:
    def __init__(self, neo4j_driver):
        self.neo4j_driver = neo4j_driver
        self.create_fulltext_index()

    def create_fulltext_index(self):
        try:
            query = """
            CREATE FULLTEXT INDEX search IF NOT EXISTS FOR (m:Memory) ON EACH [m.name, m.type, m.observations];
            """
            self.neo4j_driver.execute_query(query)
            logger.info("Created fulltext search index")
        except neo4j.exceptions.ClientError as e:
            if "An index with this name already exists" in str(e):
                logger.info("Fulltext search index already exists")
            else:
                raise e

    async def load_graph(self, filter_query="*"):
        query = """
            CALL db.index.fulltext.queryNodes('search', $filter) yield node as entity, score
            OPTIONAL MATCH (entity)-[r]-(other)
            RETURN collect(distinct {
                name: entity.name, 
                type: entity.type, 
                observations: entity.observations
            }) as nodes,
            collect(distinct {
                source: startNode(r).name, 
                target: endNode(r).name, 
                relationType: type(r)
            }) as relations
        """
        
        result = self.neo4j_driver.execute_query(query, {"filter": filter_query})
        
        if not result.records:
            return KnowledgeGraph(entities=[], relations=[])
        
        record = result.records[0]
        nodes = record.get('nodes')
        rels = record.get('relations')
        
        entities = [
            Entity(
                name=node.get('name'),
                type=node.get('type'),
                observations=node.get('observations', [])
            )
            for node in nodes if node.get('name')
        ]
        
        relations = [
            Relation(
                source=rel.get('source'),
                target=rel.get('target'),
                relationType=rel.get('relationType')
            )
            for rel in rels if rel.get('source') and rel.get('target') and rel.get('relationType')
        ]
        
        return KnowledgeGraph(entities=entities, relations=relations)

    async def create_entities(self, entities: List[Entity]) -> List[Entity]:
        query = """
        UNWIND $entities as entity
        MERGE (e:Memory { name: entity.name })
        SET e += entity {.type, .observations}
        SET e:$(entity.type)
        """
        
        entities_data = [entity.model_dump() for entity in entities]
        self.neo4j_driver.execute_query(query, {"entities": entities_data})
        return entities

    async def create_relations(self, relations: List[Relation]) -> List[Relation]:
        for relation in relations:
            query = """
            UNWIND $relations as relation
            MATCH (from:Memory),(to:Memory)
            WHERE from.name = relation.source
            AND  to.name = relation.target
            MERGE (from)-[r:$(relation.relationType)]->(to)
            """
            
            self.neo4j_driver.execute_query(
                query, 
                {"relations": [relation.model_dump() for relation in relations]}
            )
        
        return relations

    async def add_observations(self, observations: List[ObservationAddition]) -> List[Dict[str, Any]]:
        query = """
        UNWIND $observations as obs  
        MATCH (e:Memory { name: obs.entityName })
        WITH e, [o in obs.contents WHERE NOT o IN e.observations] as new
        SET e.observations = coalesce(e.observations,[]) + new
        RETURN e.name as name, new
        """
            
        result = self.neo4j_driver.execute_query(
            query, 
            {"observations": [obs.model_dump() for obs in observations]}
        )

        results = [{"entityName": record.get("name"), "addedObservations": record.get("new")} for record in result.records]
        return results

    async def delete_entities(self, entity_names: List[str]) -> None:
        query = """
        UNWIND $entities as name
        MATCH (e:Memory { name: name })
        DETACH DELETE e
        """
        
        self.neo4j_driver.execute_query(query, {"entities": entity_names})

    async def delete_observations(self, deletions: List[ObservationDeletion]) -> None:
        query = """
        UNWIND $deletions as d  
        MATCH (e:Memory { name: d.entityName })
        SET e.observations = [o in coalesce(e.observations,[]) WHERE NOT o IN d.observations]
        """
        self.neo4j_driver.execute_query(
            query, 
            {
                "deletions": [deletion.model_dump() for deletion in deletions]
            }
        )

    async def delete_relations(self, relations: List[Relation]) -> None:
        query = """
        UNWIND $relations as relation
        MATCH (source:Memory)-[r:$(relation.relationType)]->(target:Memory)
        WHERE source.name = relation.source
        AND target.name = relation.target
        DELETE r
        """
        self.neo4j_driver.execute_query(
            query, 
            {"relations": [relation.model_dump() for relation in relations]}
        )

    async def read_graph(self) -> KnowledgeGraph:
        return await self.load_graph()

    async def search_nodes(self, query: str) -> KnowledgeGraph:
        return await self.load_graph(query)

    async def find_nodes(self, names: List[str]) -> KnowledgeGraph:
        return await self.load_graph("name: (" + " ".join(names) + ")")


async def create_http_proxy(neo4j_url: str, neo4j_username: str, neo4j_password: str, 
                           neo4j_database: str, host: str = "0.0.0.0", port: int = 8000, 
                           path: str = "/mcp"):
    """Create and run the HTTP proxy server for Neo4j Memory MCP."""
    
    logger.info(f"Starting Neo4j MCP HTTP Server on {host}:{port}")

    # Connect to Neo4j
    neo4j_driver = GraphDatabase.driver(
        neo4j_url,
        auth=(neo4j_username, neo4j_password), 
        database=neo4j_database
    )
    
    # Verify connection
    try:
        neo4j_driver.verify_connectivity()
        logger.info(f"Connected to Neo4j successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        raise e

    # Initialize memory
    memory = Neo4jMemory(neo4j_driver)
    
    # Create FastMCP server
    mcp = FastMCP("mcp-neo4j-memory-http")

    @mcp.tool()
    async def create_entities(entities: List[Dict[str, Any]]) -> str:
        """Create multiple new entities in the knowledge graph"""
        try:
            entity_objects = [Entity(**entity) for entity in entities]
            result = await memory.create_entities(entity_objects)
            return json.dumps([e.model_dump() for e in result], indent=2)
        except Exception as e:
            logger.error(f"Error creating entities: {e}")
            return f"Error: {str(e)}"

    @mcp.tool()
    async def create_relations(relations: List[Dict[str, str]]) -> str:
        """Create multiple new relations between entities in the knowledge graph. Relations should be in active voice"""
        try:
            relation_objects = [Relation(**relation) for relation in relations]
            result = await memory.create_relations(relation_objects)
            return json.dumps([r.model_dump() for r in result], indent=2)
        except Exception as e:
            logger.error(f"Error creating relations: {e}")
            return f"Error: {str(e)}"

    @mcp.tool()
    async def add_observations(observations: List[Dict[str, Any]]) -> str:
        """Add new observations to existing entities in the knowledge graph"""
        try:
            observation_objects = [ObservationAddition(**obs) for obs in observations]
            result = await memory.add_observations(observation_objects)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error adding observations: {e}")
            return f"Error: {str(e)}"

    @mcp.tool()
    async def delete_entities(entityNames: List[str]) -> str:
        """Delete multiple entities and their associated relations from the knowledge graph"""
        try:
            await memory.delete_entities(entityNames)
            return "Entities deleted successfully"
        except Exception as e:
            logger.error(f"Error deleting entities: {e}")
            return f"Error: {str(e)}"

    @mcp.tool()
    async def delete_observations(deletions: List[Dict[str, Any]]) -> str:
        """Delete specific observations from entities in the knowledge graph"""
        try:
            deletion_objects = [ObservationDeletion(**deletion) for deletion in deletions]
            await memory.delete_observations(deletion_objects)
            return "Observations deleted successfully"
        except Exception as e:
            logger.error(f"Error deleting observations: {e}")
            return f"Error: {str(e)}"

    @mcp.tool()
    async def delete_relations(relations: List[Dict[str, str]]) -> str:
        """Delete multiple relations from the knowledge graph"""
        try:
            relation_objects = [Relation(**relation) for relation in relations]
            await memory.delete_relations(relation_objects)
            return "Relations deleted successfully"
        except Exception as e:
            logger.error(f"Error deleting relations: {e}")
            return f"Error: {str(e)}"

    @mcp.tool()
    async def read_graph() -> str:
        """Read the entire knowledge graph"""
        try:
            result = await memory.read_graph()
            return json.dumps(result.model_dump(), indent=2)
        except Exception as e:
            logger.error(f"Error reading graph: {e}")
            return f"Error: {str(e)}"

    @mcp.tool()
    async def search_nodes(query: str) -> str:
        """Search for nodes in the knowledge graph based on a query"""
        try:
            result = await memory.search_nodes(query)
            return json.dumps(result.model_dump(), indent=2)
        except Exception as e:
            logger.error(f"Error searching nodes: {e}")
            return f"Error: {str(e)}"

    @mcp.tool()
    async def find_nodes(names: List[str]) -> str:
        """Find specific nodes in the knowledge graph by their names"""
        try:
            result = await memory.find_nodes(names)
            return json.dumps(result.model_dump(), indent=2)
        except Exception as e:
            logger.error(f"Error finding nodes: {e}")
            return f"Error: {str(e)}"

    @mcp.tool()
    async def open_nodes(names: List[str]) -> str:
        """Open specific nodes in the knowledge graph by their names"""
        try:
            result = await memory.find_nodes(names)
            return json.dumps(result.model_dump(), indent=2)
        except Exception as e:
            logger.error(f"Error opening nodes: {e}")
            return f"Error: {str(e)}"

    # Health check endpoint
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request) -> dict:
        return {"status": "healthy", "service": "mcp-neo4j-memory-http"}
    
    # Start server
    logger.info(f"Server running: http://{host}:{port}/sse")
    await mcp.run_async(transport="sse", host=host, port=port, log_level="info") 