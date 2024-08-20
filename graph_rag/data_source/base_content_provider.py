import logging
from abc import ABC, abstractmethod

from graph_rag.data_model import ProcessedData

logger = logging.getLogger(__name__)


class ContentProvider(ABC):
    def __init__(self):
        logger.info(f"{self.__class__.__name__} initialized")

    @abstractmethod
    def _fetch_data(self) -> ProcessedData: ...

    def fetch_data(self) -> ProcessedData:
        logger.info(f"Fetching data from {self.__class__.__name__}")
        return self._fetch_data()
