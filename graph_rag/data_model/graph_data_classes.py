from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from graph_rag.data_model import Cacheable


class RelationType(Enum):
    CONTAINS = "CONTAINS"
    REFERENCES = "REFERENCES"
    HAS_CHUNK = "HAS_CHUNK"


class PageType(Enum):
    PAGE = "Page"
    DATABASE = "Database"
    BOOKMARK = "Bookmark"
    CHUNK = "Chunk"


def get_page_type_from_string(page_type_str: str) -> PageType:
    return PageType[page_type_str.upper()]


def get_relation_type_from_string(relation_type_str: str) -> RelationType:
    return RelationType[relation_type_str.upper()]


@dataclass
class Chunk(Cacheable):
    @classmethod
    def get_class_version(cls) -> int:
        return 1

    content: str
    embedding: list[float]


@dataclass
class GraphPage(Cacheable):
    id: str
    title: str
    type: PageType
    url: str
    content: Optional[str] = None
    source: str = 'Notion'
    last_edited_time: Optional[str] = None
    chunks: list[Chunk] = field(default_factory=list)

    @classmethod
    def get_class_version(cls) -> int:
        return 1


@dataclass
class GraphRelation(Cacheable):
    from_page_id: str
    relation_type: RelationType
    to_page_id: str
    context: Optional[str] = None

    @classmethod
    def get_class_version(cls) -> int:
        return 1


@dataclass
class ProcessedData:
    pages: dict[str, GraphPage]
    relations: list[GraphRelation]
