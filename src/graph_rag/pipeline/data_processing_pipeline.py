import logging
from typing import Dict, List

from src.graph_rag.data_model.notion_page import NotionPage, NotionRelation, PageType
from src.graph_rag.ai_agent.base_agent import BaseAgent
from src.graph_rag.config.config_manager import Config
from src.graph_rag.processor.entity_extractor import EntityExtractor
from src.graph_rag.processor.notion_processor import NotionProcessor
from src.graph_rag.storage.neo4j_manager import Neo4jManager

logger = logging.getLogger(__name__)


class DataProcessingPipeline:
    def __init__(self):
        self.notion_processor = NotionProcessor()
        self.entity_extractor = EntityExtractor()
        self.neo4j_manager = Neo4jManager()
        self.ai_agent = BaseAgent()

    def process_notion_page(self, page_id):
        # Process the Notion page
        self.notion_processor.process_pages(page_id)
        prepared_pages = self.notion_processor.prepared_pages
        logger.info(f"Prepared {len(prepared_pages)} pages from Notion")
        relations = self.notion_processor.page_relations
        logger.info(f"Prepared {len(relations)} relations from Notion")

        for page in prepared_pages.values():
            self.neo4j_manager.create_page_node(page.id, page.title, page.type.value, page.content, page.url, page.source)

        """ Cleaning up relations without existing pages """
        relations = [relation for relation in relations if relation.from_page_id in prepared_pages and relation.to_page_id in prepared_pages]

        for relation in relations:
            self.neo4j_manager.link_entities(relation.from_page_id, relation.to_page_id, relation.relation_type.value, relation.context)

        logging.info("Notion structure has been parsed and stored in Neo4j.")

    def process_content(self, content_data):
        page_id = content_data['page_id']
        title = content_data['title']
        content = content_data['content']

        # Store page in Neo4j
        self.neo4j_manager.create_page_node(page_id, title, content)

        # Extract entities
        entities = self.entity_extractor.extract_entities(content)

        # Store entities and link to page
        for entity_type, entity_list in entities.items():
            for entity_name in entity_list:
                self.neo4j_manager.create_entity_node(entity_type, entity_name)
                self.neo4j_manager.link_page_to_entity(page_id, entity_type, entity_name)

        # Generate insights using AI agent
        insight_prompt = f"Generate a brief insight about the following content:\n\n{content[:1000]}..."
        insight = self.ai_agent.generate_response(insight_prompt)

        # Get related pages for the first entity (as an example)
        if entities:
            first_entity_type = list(entities.keys())[0]
            first_entity_name = entities[first_entity_type][0]
            related_pages = self.neo4j_manager.get_related_pages(first_entity_type, first_entity_name)
        else:
            related_pages = []

        # Get entity relationships for the first entity (as an example)
        if entities:
            entity_relationships = self.neo4j_manager.get_entity_relationships(first_entity_type, first_entity_name)
        else:
            entity_relationships = []

        return {
            "page_id": page_id,
            "title": title,
            "entities": entities,
            "insight": insight,
            "related_pages": related_pages,
            "entity_relationships": entity_relationships
        }
