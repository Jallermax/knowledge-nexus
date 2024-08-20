import logging
from abc import ABC, abstractmethod

from graph_rag.config import Config
from graph_rag.data_model import ProcessedData

logger = logging.getLogger(__name__)


class Processor(ABC):
    def __init__(self):
        self.config = Config()
        logger.info(f"{self.__class__.__name__} initialized")

    @abstractmethod
    def _process(self, processed_content: ProcessedData):
        ...

    def process_data(self, processed_content: ProcessedData):
        logger.info(f"Processing started with {self.__class__.__name__}")
        self._process(processed_content)
