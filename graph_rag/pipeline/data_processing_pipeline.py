import logging
from typing import Dict, List

from graph_rag.config.config_manager import Config
from graph_rag.data_model.graph_data_classes import GraphPage, GraphRelation, PageType, ProcessedData
from graph_rag.data_source.base_content_provider import ContentProvider
from graph_rag.processor.base_processor import Processor
from graph_rag.processor.entity_extractor import EntityExtractor
from graph_rag.processor.notion_processor import NotionProcessor
from graph_rag.storage.neo4j_manager import Neo4jManager
from graph_rag.utils.logging import LoggingProgressBar, ProgressBarHandler

logger = logging.getLogger(__name__)


class DataProcessingPipeline:
    def __init__(self):
        self.config = Config()
        self.notion_processor = NotionProcessor()
        self.entity_extractor = EntityExtractor()
        self.neo4j_manager = Neo4jManager()
        self.data_sources: List[ContentProvider] = []
        self.processors: List[Processor] = []

    def process_notion_page(self, page_id):
        # Process the Notion page
        self.notion_processor.process_pages(page_id)
        prepared_pages = self.notion_processor.prepared_pages
        logger.info(f"Prepared {len(prepared_pages)} pages from Notion")
        relations = self.notion_processor.page_relations
        logger.info(f"Prepared {len(relations)} relations from Notion")

        for page in prepared_pages.values():
            self.neo4j_manager.create_page_node(page)

        # TODO check existing pages not only in prepared_pages, but in neo4j as well

        if self.config.NOTION_CREATE_UNPROCESSED_NODES:
            self.add_missing_pages(prepared_pages, relations)
        else:
            relations = self.clean_orphan_relations(prepared_pages, relations)

        for relation in relations:
            self.neo4j_manager.link_entities(relation)

        logger.info("Notion structure has been parsed and stored in Neo4j.")

    def add_missing_pages(self, prepared_pages: Dict[str, GraphPage], relations: List[GraphRelation]):
        logger.info("Adding unprocessed pages from relations to prepared_pages")
        missing_page_count = 0
        for relation in relations:
            is_from_page_prepared = relation.from_page_id in prepared_pages
            is_to_page_prepared = relation.to_page_id in prepared_pages
            if not is_from_page_prepared:
                self.add_missing_page(relation.from_page_id, prepared_pages, prepared_pages[
                    relation.to_page_id].source if is_to_page_prepared else 'Unknown')
                missing_page_count += 1

            if not is_to_page_prepared:
                self.add_missing_page(relation.to_page_id, prepared_pages, prepared_pages[
                    relation.from_page_id].source if is_from_page_prepared else 'Unknown')
                missing_page_count += 1
        logger.info(f"{missing_page_count} unprocessed pages from relations was added to graph")

    def add_missing_page(self, page_id: str, prepared_pages: Dict[str, GraphPage], source: str = 'Unknown'):
        new_page = GraphPage(
            id=page_id,
            title="Unprocessed",
            type=PageType.PAGE,
            url='',
            source=source
        )
        logger.info(f"Adding unprocessed page {page_id}")
        self.neo4j_manager.create_page_node(new_page)
        prepared_pages[page_id] = new_page

    def add_data_source(self, data_source: ContentProvider):
        self.data_sources.append(data_source)

    def add_processor(self, processor: Processor):
        self.processors.append(processor)

    def run(self):
        # Step 1: Fetch data from all sources
        processed_data = ProcessedData(pages={}, relations=[])
        pages = processed_data.pages
        relations = processed_data.relations
        for data_source in self.data_sources:
            source_data = data_source.fetch_data()
            pages.update(source_data.pages)
            relations.extend(source_data.relations)

        # Step 2: Run all processors
        for processor in self.processors:
            processor.process(processed_data)

        # Step 3: Save data to Neo4j graph
        self.create_processed_page_nodes([p for p in processed_data.pages.values()])

        if self.config.NOTION_CREATE_UNPROCESSED_NODES:
            self.add_missing_pages(processed_data.pages, processed_data.relations)
        else:
            processed_data.relations = self.clean_orphan_relations(processed_data.pages, processed_data.relations)

        for relation in processed_data.relations:
            self.neo4j_manager.link_entities(relation)

        logger.info("Notion structure has been parsed and stored in Neo4j.")

    def create_processed_page_nodes(self, processed_pages: List[GraphPage]) -> None:
        progress_bar = LoggingProgressBar(len(processed_pages), prefix='Processing:',
                                          suffix=f"pages saved to graph out of {len(processed_pages)} pages ", length=50)
        handler = ProgressBarHandler(progress_bar)
        logger.addHandler(handler)
        progress_bar.start()

        for page in processed_pages:
            self.neo4j_manager.create_page_node(page)
            progress_bar.update()

        progress_bar.finish()
        logger.removeHandler(handler)

    @staticmethod
    def clean_orphan_relations(pages, relations):
        """ Cleaning up relations without existing pages """
        relations_count_before = len(relations)
        relations = [relation for relation in relations if
                     relation.from_page_id in pages and relation.to_page_id in pages]
        logger.info(f"{len(relations) - relations_count_before} Relations with unprocessed pages was deleted")
        return relations
