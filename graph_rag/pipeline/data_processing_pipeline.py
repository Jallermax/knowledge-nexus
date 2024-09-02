import logging

from graph_rag.config import Config
from graph_rag.data_model import ProcessedData
from graph_rag.data_source import ContentProvider
from graph_rag.processor import Processor

logger = logging.getLogger(__name__)


class DataProcessingPipeline:
    def __init__(self):
        self.config = Config()
        self.data_sources: list[ContentProvider] = []
        self.processors: list[Processor] = []

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
            processor.process_data(processed_data)
