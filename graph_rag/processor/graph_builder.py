import logging

from graph_rag.data_model import ProcessedData, GraphPage, PageType, GraphRelation
from graph_rag.processor import Processor
from graph_rag.storage import Neo4jManager
from graph_rag.utils.logging import LoggingProgressBar, ProgressBarHandler

logger = logging.getLogger(__name__)


class GraphBuilder(Processor):
    def __init__(self):
        super().__init__()
        self.neo4j_manager = Neo4jManager()

    def _process(self, processed_data: ProcessedData):
        self.neo4j_manager.create_vector_index()

        self.create_processed_page_nodes([p for p in processed_data.pages.values()])

        self.handle_orphan_relations(processed_data)

        for relation in processed_data.relations:
            self.neo4j_manager.link_entities(relation)

        logger.info("Notion structure has been parsed and stored in Neo4j.")

    def handle_orphan_relations(self, processed_data: ProcessedData):
        if self.config.NOTION_CREATE_UNPROCESSED_NODES:
            self.add_missing_pages(processed_data.pages, processed_data.relations)
        else:
            processed_data.relations = self.clean_orphan_relations(processed_data.pages, processed_data.relations)

    def add_missing_pages(self, prepared_pages: dict[str, GraphPage], relations: list[GraphRelation]):
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

    def add_missing_page(self, page_id: str, prepared_pages: dict[str, GraphPage], source: str = 'Unknown'):
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

    def create_processed_page_nodes(self, processed_pages: list[GraphPage]) -> None:
        progress_bar = LoggingProgressBar(len(processed_pages), prefix='Processing:',
                                          suffix=f"pages saved to graph out of {len(processed_pages)} pages ",
                                          length=50)
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
