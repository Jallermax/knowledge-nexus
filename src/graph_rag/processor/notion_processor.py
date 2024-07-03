import logging
import re
from typing import Dict, List

from src.graph_rag.config.config_manager import Config
from src.graph_rag.data_model.notion_page import NotionPage, get_page_type_from_string, NotionRelation, RelationType, PageType
from src.graph_rag.data_source.notion_api import NotionAPI
from src.graph_rag.data_source.web_scraper import get_info_from_url

logger = logging.getLogger(__name__)


def _extract_uuid(href):
    pattern = r"(https:\/\/www\.notion\.so)?/([a-zA-Z0-9\-]+/)?([a-zA-Z0-9\-]+-)?([a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12})(\?[a-zA-Z0-9%=\-&]*)?"
    match = re.match(pattern, href)
    if match:
        return match.group(4)  # return the UUID

    else:
        return None  # return None if the href does not match the pattern


def _extract_title(page_content: dict):
    if 'title' in page_content and page_content['title']:
        return page_content['title'][0]['plain_text']
    else:
        return 'Untitled'


def _extract_rich_text(rich_text: List[dict]):
    return ''.join([text['plain_text'] for text in rich_text])


class NotionProcessor:
    def __init__(self):
        self.notion_api = NotionAPI()
        self.config = Config()
        self.prepared_pages: Dict[str, NotionPage] = {}
        self.page_relations: List[NotionRelation] = []
        logger.info("NotionProcessor initialized")

    def process_pages(self, root_page_id: str):
        logger.info(f"Processing root page: {root_page_id}")
        root_page = self.notion_api.get_root_page_info(root_page_id)
        notion_page = NotionPage(root_page['id'], _extract_title(root_page), get_page_type_from_string(root_page['object']),
                                 root_page['url'])
        self.prepared_pages.update({root_page['id']: notion_page})
        self.recursive_process_page_children(root_page)

    def recursive_process_page_children(self, page_info: dict, recursive_depth: int = 0):
        """
        Recursively process all blocks of the given page and its sub-pages if this page hasn't been processed before (not in self.processed_pages).
        Add every proccesed sub-page into processed_pages and add relation to page_relations
        If is_database, then make additional call of get_all_database_items to get all db pages
        """
        recursive_depth += 1
        if recursive_depth >= self.config.NOTION_PAGE_MAX_DEPTH:
            logger.warning(
                f"Current recursion depth {recursive_depth} for processing pages exceeded depth limit. See notion_api.page_max_depth in config.yaml")
            return
        is_database = page_info['object'] == 'database'
        logger.debug(f"[Depth={recursive_depth}] Recursively processing page: {page_info['id']}, is_database: {is_database}")
        if is_database:
            child_db_pages = self.notion_api.get_all_database_items(page_info['id'])
            for child_page in child_db_pages:
                self.page_relations.append(NotionRelation(page_info['id'], RelationType.CONTAINS, child_page['id']))
                self.recursive_process_unprocessed_page(child_page['id'], page_info=child_page, recursive_depth=recursive_depth)

        self.recursive_process_properties(page_info)

        try:
            child_blocks = self.notion_api.get_all_content_blocks(page_info['id'])
        except Exception as e:
            logger.error(f"[Depth={recursive_depth}] Exception occurred during fetching of page {page_info['id']} blocks: {e}")
            logger.debug(f"Stack_trace for {page_info['id']} exception", stack_info=True, stacklevel=15)
            return
        for block in child_blocks:
            self.recursive_process_block(block, parent_id=page_info['id'], recursive_depth=recursive_depth)

    def recursive_process_block(self, block: dict, parent_id: str, recursive_depth: int = 0):
        recursive_depth += 1
        logger.debug(f"[Depth={recursive_depth}] Recursively parsing block: {block['id']}, parent_id: {parent_id}")
        unsupported_block_types = [
            'breadcrumb',
            'column',  # retrieve block children for content
            'column_list',  # retrieve block children for columns
            'divider',
            'equation',
            'file',
            'image',
            'pdf',
            'synced_block',
            'table',
            'table_row',
            'table_of_contents',
            'video',
        ]
        url_block_types = [
            'bookmark',
            'embed',
            'link_preview',
        ]
        rich_text_block_types = [
            'bulleted_list_item',
            'callout',
            'code',
            'heading_1',
            'heading_2',
            'heading_3',
            'numbered_list_item',
            'paragraph',
            'quote',
            'template',
            'to_do',
            'toggle',
        ]
        if block['type'] in ['child_page', 'child_database']:
            self.page_relations.append(NotionRelation(parent_id, RelationType.CONTAINS, block['id']))
            self.recursive_process_unprocessed_page(block['id'], block['type'] == 'child_database', recursive_depth=recursive_depth)

        elif block['type'] == 'link_to_page':
            uuid = block['link_to_page'][block['link_to_page']['type']]
            self.page_relations.append(NotionRelation(parent_id, RelationType.REFERENCES, uuid))
            self.recursive_process_unprocessed_page(uuid, recursive_depth=recursive_depth)

        elif block['type'] in rich_text_block_types:
            rich_text_array = block[block['type']]['rich_text']
            for text in rich_text_array:
                # TODO parse each type of rich_text individually to extract page id
                if 'href' in text and text['href']:
                    uuid = _extract_uuid(text['href'])
                    if uuid:
                        self.page_relations.append(NotionRelation(parent_id, RelationType.REFERENCES, uuid,
                                                                  context=_extract_rich_text(rich_text_array)))
                        self.recursive_process_unprocessed_page(uuid, recursive_depth=recursive_depth)
                    else:
                        self.page_relations.append(NotionRelation(parent_id, RelationType.REFERENCES, text['href'],
                                                                  context=_extract_rich_text(rich_text_array)))
                        self.process_unprocessed_bookmark(text['href'], recursive_depth=recursive_depth)

        elif block['type'] in url_block_types:
            url = block[block['type']]['url']
            self.page_relations.append(NotionRelation(parent_id, RelationType.REFERENCES, url))
            self.process_unprocessed_bookmark(url)

        elif block['type'] == 'unsupported':
            logger.warning(f"Unsupported block_id {block['id']} of page {parent_id}")
            return

        if 'has_children' in block and block['has_children']:
            try:
                child_blocks = self.notion_api.get_all_content_blocks(block['id'])
            except Exception as e:
                logger.error(f"[Depth={recursive_depth}] Exception occurred during fetching of page {block['id']} blocks: {e}")
                logger.debug(f"Stack_trace for {block['id']} exception", stack_info=True, stacklevel=15)
                return
            for child_block in child_blocks:
                self.recursive_process_block(child_block, parent_id, recursive_depth)

    def process_unprocessed_bookmark(self, url: str, recursive_depth: int = 0):
        recursive_depth += 1
        logger.debug(f"[Depth={recursive_depth}] Recursively parsing bookmark: {url}")
        if url not in self.prepared_pages.keys():
            try:
                title, description = get_info_from_url(url)
            except:
                title, description = '', ''
            bookmark_page = NotionPage(url, title, PageType.BOOKMARK, url, content=description, source='Web')
            self.prepared_pages.update({url: bookmark_page})

    def recursive_process_unprocessed_page(self, page_id: str, is_database: bool = None, page_info: dict = None, recursive_depth: int = 0):
        if page_id in self.prepared_pages.keys():
            return

        if not page_info:
            try:
                if is_database is None:
                    page_info = self.notion_api.get_root_page_info(page_id)
                elif is_database:
                    page_info = self.notion_api.get_database_metadata(page_id)
                else:
                    page_info = self.notion_api.get_page_metadata(page_id)
            except Exception as e:
                # TODO Is it needed to add page to prepared_pages if it failed to get page info? To keep consistent relations
                logger.error(f"[Depth={recursive_depth}] Failed to get page info for page: {page_id}: {e}")
                logger.debug(f"Stack_trace for {page_id} exception", stack_info=True, stacklevel=15)
                return

        page = NotionPage(page_id, _extract_title(page_info), get_page_type_from_string(page_info['object']), page_info['url'])
        logger.info(f"[Depth={recursive_depth}] Adding new processed page: {page.title}({page.type};{page.id})")
        self.prepared_pages.update({page_id: page})
        if page_info['archived'] or page_info['in_trash']:
            logger.warning(f"[Depth={recursive_depth}] Object {page_info['object']} (id:{page_info['id']} is archived or in trash")
            page.title = f"[ARCHIVED] {page.title}"
            return

        self.recursive_process_page_children(page_info, recursive_depth=recursive_depth)

    def _process_block_md(self, block: dict):
        content = ""
        if block['type'] == 'paragraph':
            content += _extract_rich_text(block['paragraph']['rich_text'])
        elif block['type'].startswith('heading_'):
            content += _extract_rich_text(block[block['type']]['rich_text'])
        elif block['type'] == 'bulleted_list_item':
            content += "• " + _extract_rich_text(block['bulleted_list_item']['rich_text'])
        elif block['type'] == 'numbered_list_item':
            content += "1. " + _extract_rich_text(block['numbered_list_item']['rich_text'])

        content += "\n"

        if 'has_children' in block and block['has_children']:
            child_blocks = self.notion_api.get_all_content_blocks(block['id'])
            for child_block in child_blocks:
                content += self._process_block_md(child_block)

        return content

    def recursive_process_properties(self, page_info: dict):
        # TODO: Implement processing of properties
        pass
