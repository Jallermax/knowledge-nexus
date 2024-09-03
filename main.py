import logging
import os

import dotenv

from graph_rag.pipeline import DataProcessingPipeline
from graph_rag.processor import ContentChunkerAndEmbedder
from graph_rag.processor.graph_builder import GraphBuilder
from graph_rag.storage import Neo4jManager
from graph_rag.data_source import NotionProvider
from graph_rag.pipeline import DataProcessingPipeline

dotenv.load_dotenv()

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    # manager = Neo4jManager()
    # manager.clean_database()
    pipeline = DataProcessingPipeline()

    # Add data sources
    pipeline.add_data_source(NotionProvider())

    # Add processors
    pipeline.add_processor(ContentChunkerAndEmbedder())
    pipeline.add_processor(GraphBuilder())

    # Run the pipeline
    pipeline.run()


if __name__ == "__main__":
    main()
