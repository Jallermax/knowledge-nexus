from langchain_community.graphs.neo4j_graph import Neo4jGraph
from src.config.config_manager import Config

class Neo4jManager:
    def __init__(self):
        self.config = Config()
        self.graph = Neo4jGraph(
            url=f"bolt://{self.config.NEO4J_HOST}:{self.config.NEO4J_PORT}",
            username=self.config.NEO4J_USER,
            password=self.config.NEO4J_PASSWORD
        )

    def close(self):
        self.graph.close()

    def create_page_node(self, page_id, title, content):
        query = (
            "MERGE (p:Page {id: $page_id}) "
            "SET p.title = $title, p.content = $content"
        )
        self.graph.query(query, {'page_id': page_id, 'title': title, 'content': content})

    def create_entity_node(self, entity_type, entity_name):
        query = (
            f"MERGE (e:{entity_type} {{name: $entity_name}}) "
            "RETURN e"
        )
        self.graph.query(query, {'entity_name': entity_name})

    def link_page_to_entity(self, page_id, entity_type, entity_name):
        query = (
            f"MATCH (p:Page {{id: $page_id}}), (e:{entity_type} {{name: $entity_name}}) "
            "MERGE (p)-[:MENTIONS]->(e)"
        )
        self.graph.query(query, {'page_id': page_id, 'entity_name': entity_name})

    def get_entities_for_page(self, page_id):
        query = (
            "MATCH (p:Page {id: $page_id})-[:MENTIONS]->(e) "
            "RETURN labels(e) AS entity_type, e.name AS entity_name"
        )
        result = self.graph.query(query, {'page_id': page_id})
        return [{'type': row['entity_type'][0], 'name': row['entity_name']} for row in result]

    def get_related_pages(self, entity_type, entity_name, limit=5):
        query = (
            f"MATCH (e:{entity_type} {{name: $entity_name}})<-[:MENTIONS]-(p:Page) "
            "RETURN p.id AS page_id, p.title AS page_title "
            "LIMIT $limit"
        )
        result = self.graph.query(query, {'entity_name': entity_name, 'limit': limit})
        return [{'id': row['page_id'], 'title': row['page_title']} for row in result]

    def get_entity_relationships(self, entity_type, entity_name):
        query = (
            f"MATCH (e1:{entity_type} {{name: $entity_name}})-[:MENTIONS*2]-(e2) "
            "WHERE e1 <> e2 "
            "RETURN labels(e2) AS related_type, e2.name AS related_name, "
            "count(*) AS strength "
            "ORDER BY strength DESC "
            "LIMIT 10"
        )
        result = self.graph.query(query, {'entity_name': entity_name})
        return [{'type': row['related_type'][0], 'name': row['related_name'], 'strength': row['strength']} for row in result]
