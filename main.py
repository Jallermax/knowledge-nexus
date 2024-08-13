import logging

import dotenv

from graph_rag.pipeline.data_processing_pipeline import DataProcessingPipeline
from graph_rag.processor.content_chunker_and_embedder import ContentChunkerAndEmbedder
from graph_rag.processor.notion_processor import NotionProcessor
from graph_rag.storage.neo4j_manager import Neo4jManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

dotenv.load_dotenv()


def main():
    # manager = Neo4jManager()
    # manager.clean_database()
    pipeline = DataProcessingPipeline()

    # Add data sources
    pipeline.add_data_source(NotionProcessor())

    # Add processors
    pipeline.add_processor(ContentChunkerAndEmbedder())

    # Run the pipeline
    pipeline.run()


if __name__ == "__main__":
    main()
