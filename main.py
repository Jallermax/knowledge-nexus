import logging
import os

import dotenv

from graph_rag.pipeline.data_processing_pipeline import DataProcessingPipeline
from graph_rag.storage.neo4j_manager import Neo4jManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

dotenv.load_dotenv()


def main():
    manager = Neo4jManager()
    pipeline = DataProcessingPipeline()

    notion_page_id = os.getenv('NOTION_ROOT_PAGE_ID')
    manager.clean_database()
    pipeline.process_notion_page(notion_page_id)


if __name__ == "__main__":
    main()
