import logging

import dotenv

from graph_rag.pipeline import DataProcessingPipeline
from graph_rag.processor import ContentChunkerAndEmbedder
from graph_rag.storage import Neo4jManager
from graph_rag.data_source import NotionProvider

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

dotenv.load_dotenv()


def main():
    # manager = Neo4jManager()
    # manager.clean_database()
    pipeline = DataProcessingPipeline()

    # Add data sources
    pipeline.add_data_source(NotionProvider())

    # Add processors
    pipeline.add_processor(ContentChunkerAndEmbedder())

    # Run the pipeline
    pipeline.run()


if __name__ == "__main__":
    main()
