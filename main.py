import logging
from graph_rag.pipeline.data_processing_pipeline import DataProcessingPipeline
from graph_rag.storage.neo4j_manager import Neo4jManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    manager = Neo4jManager()
    pipeline = DataProcessingPipeline()

    # Replace with an actual Notion page ID
    notion_page_id = "your_notion_page_id_here"

    manager.clean_database()
    pipeline.process_notion_page(notion_page_id)


if __name__ == "__main__":
    main()
