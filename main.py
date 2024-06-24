from src.pipeline.data_processing_pipeline import DataProcessingPipeline

def main():
    pipeline = DataProcessingPipeline()

    # Replace with an actual Notion page ID
    notion_page_id = "your_notion_page_id_here"

    result = pipeline.process_notion_page(notion_page_id)

    print(f"Processed page: {result['title']}")
    print(f"Extracted entities: {result['entities']}")
    print(f"Generated insight: {result['insight']}")

    if result['related_pages']:
        print("\nRelated pages:")
        for page in result['related_pages']:
            print(f"- {page['title']} (ID: {page['id']})")

    if result['entity_relationships']:
        print("\nEntity relationships:")
        for relation in result['entity_relationships']:
            print(f"- {relation['type']} {relation['name']} (Strength: {relation['strength']})")

if __name__ == "__main__":
    main()
