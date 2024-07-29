from abc import ABC

from graph_rag.config.config_manager import Config
from graph_rag.data_model.graph_data_classes import ProcessedData


class Processor(ABC):
    def __init__(self):
        self.config = Config()

    def process(self, processed_content: ProcessedData):
        pass
