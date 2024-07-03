from enum import Enum


class RelationType(Enum):
    CONTAINS = "CONTAINS"
    REFERENCES = "REFERENCES"


class PageType(Enum):
    PAGE = "Page"
    DATABASE = "Database"
    BOOKMARK = "Bookmark"


def get_page_type_from_string(page_type_str: str) -> PageType:
    return PageType[page_type_str.upper()]


class NotionPage:
    def __init__(self, page_id: str, title: str, page_type: PageType, url: str, content: str = None, source: str = 'Notion'):
        self.id: str = page_id
        self.title: str = title
        self.type: PageType = page_type
        self.url: str = url
        self.content: str = content
        self.source: str = source


class NotionRelation:
    def __init__(self, from_page_id: str, relation_type: RelationType, to_page_id: str, context: str = None):
        self.from_page_id: str = from_page_id
        self.relation_type: RelationType = relation_type
        self.to_page_id: str = to_page_id
        self.context: str = context
