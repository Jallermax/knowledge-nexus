from abc import ABC, abstractmethod

from graph_rag.data_model.graph_data_classes import ProcessedData


class ContentProvider(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def fetch_data(self) -> ProcessedData: ...
