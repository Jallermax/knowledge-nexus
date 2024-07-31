import logging

from langchain_community.graphs.neo4j_graph import Neo4jGraph

from graph_rag.config.config_manager import Config
from graph_rag.data_model.graph_data_classes import GraphRelation, GraphPage, Chunk, PageType, RelationType

logger = logging.getLogger(__name__)


class Neo4jManager:
    def __init__(self):
        self.config = Config()
        self.graph = Neo4jGraph(
            url=self.config.NEO4J_URI,
            username=self.config.NEO4J_USER,
            password=self.config.NEO4J_PASSWORD
        )

    def clean_database(self):
        self.graph.query("MATCH (n) DETACH DELETE n")
        logger.info("Database has been cleaned")
        self.create_vector_index()

    def create_vector_index(self):
        constraint_query = (
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS "
            f"FOR (c:{PageType.CHUNK.value}) REQUIRE c.id IS UNIQUE"
        )
        self.graph.query(constraint_query)

        # Create the vector index if it doesn't exist
        index_query = (
            "CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS "
            f"FOR (c:{PageType.CHUNK.value}) "
            "ON (c.embedding) "
            f"OPTIONS {{indexConfig: {{`vector.dimensions`: {self.config.EMBEDDINGS_DIMENSIONS}, `vector.similarity_function`: 'cosine'}}}}"
        )
        try:
            self.graph.query(index_query)
            logger.info("Vector index 'chunk_embedding' created or already exists")
        except Exception as e:
            logger.error(f"Failed to create vector index: {str(e)}")

    def check_page_exists(self, page_id: str) -> str | None:
        query = (
            "MATCH (p) WHERE p.id = $page_id "
            "RETURN p.last_edited_time AS last_edited_time"
        )
        result = self.graph.query(query, {'page_id': page_id})
        if result:
            return result[0]['last_edited_time']
        return None

    def create_page_node(self, page: GraphPage):
        existing_last_edited_time = self.check_page_exists(page.id)

        if existing_last_edited_time and page.last_edited_time == existing_last_edited_time:
            logger.debug(f"Page {page.id} already exists with a newer or equal last_edited_time. Skipping update.")
            return

        query = (
            f"MERGE (p:{page.type.value} {{id: $page_id}}) "
            "SET p.title = $title, p.content = $content, p.url = $url, p.source = $source, "
            "p.last_edited_time = $last_edited_time"
        )
        self.graph.query(query, {'page_id': page.id,
                                 'title': page.title,
                                 'content': page.content,
                                 'url': page.url,
                                 'source': page.source,
                                 'last_edited_time': page.last_edited_time})

        # Remove existing chunks
        self.remove_page_chunks(page.id)

        # Create chunk nodes and link them to the page
        if page.chunks:
            self.create_chunk_nodes(page.id, page.chunks)

    def remove_page_chunks(self, page_id: str):
        query = (
            f"MATCH (p)-[r:{RelationType.HAS_CHUNK.value}]->(c:{PageType.CHUNK.value}) "
            "WHERE p.id = $page_id "
            "DELETE r, c"
        )
        self.graph.query(query, {'page_id': page_id})

    def create_chunk_nodes(self, page_id: str, chunks: list[Chunk]):
        for i, chunk in enumerate(chunks):
            query = (
                "MATCH (p) WHERE p.id = $page_id "
                f"CREATE (c:{PageType.CHUNK.value} {{content: $content, embedding: $embedding, sequence: $sequence}}) "
                f"CREATE (p)-[:{RelationType.HAS_CHUNK.value}]->(c)"
            )
            self.graph.query(query, {
                'page_id': page_id,
                'content': chunk.content,
                'embedding': chunk.embedding,
                'sequence': i
            })

    def link_entities(self, relation: GraphRelation):
        query = (
            "MATCH (e1) WHERE (e1:Page OR e1:Database OR e1:Bookmark) AND e1.id = $entity_id_1 "
            "MATCH (e2) WHERE (e2:Page OR e2:Database OR e2:Bookmark) AND e2.id = $entity_id_2 "
            f"MERGE (e1)-[:{relation.relation_type.value} {{context: $context}}]->(e2)"
        )
        self.graph.query(query, {'entity_id_1': relation.from_page_id,
                                 'entity_id_2': relation.to_page_id,
                                 'context': relation.context if relation.context else ''})

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
        return [{'type': row['related_type'][0], 'name': row['related_name'], 'strength': row['strength']} for row in
                result]
