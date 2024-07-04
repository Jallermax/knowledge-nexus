import logging
import re
from typing import Dict, List

from graph_rag.config.config_manager import Config
from graph_rag.data_model.notion_page import NotionPage, get_page_type_from_string, NotionRelation, RelationType, PageType
from graph_rag.data_source.notion_api import NotionAPI
from graph_rag.data_source.web_scraper import get_info_from_url

logger = logging.getLogger(__name__)


def _extract_notion_uuid(href):
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
        for prop_name in page_content['properties']:
            prop = page_content['properties'][prop_name]
            if prop['type'] == 'title' and 'title' in prop and prop['title']:
                return prop['title'][0]['plain_text']
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
                                 root_page['url'], last_edited_time=root_page['last_edited_time'])
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

        # TODO add parse comments
        if is_database:
            # TODO parse mentions in db title and relations in db properies
            child_db_pages = self.notion_api.get_all_database_items(page_info['id'])
            for child_page in child_db_pages:
                self.save_relation_and_process_page(
                    parent_id=page_info['id'],
                    rel_type=RelationType.CONTAINS,
                    page_id=child_page['id'],
                    page_info=child_page,
                    recursive_depth=recursive_depth)
        else:
            self.recursive_process_page_properties(page_info, recursive_depth)

        try:
            child_blocks = self.notion_api.get_all_content_blocks(page_info['id'])
        except Exception as e:
            logger.error(f"[Depth={recursive_depth}] Exception occurred during fetching of page {page_info['id']} blocks: {e}")
            logger.debug(f"Stack_trace for {page_info['id']} exception", stack_info=True, stacklevel=15)
            return
        for block in child_blocks:
            self.recursive_process_block(block, parent_id=page_info['id'], recursive_depth=recursive_depth)

    def save_relation_and_process_page(self, parent_id: str, rel_type: RelationType, page_id: str, rel_context: str = None,
                                       is_database: bool = None, page_info: dict = None, recursive_depth: int = 0):
        self.page_relations.append(NotionRelation(parent_id, rel_type, page_id, rel_context))
        self.recursive_process_unprocessed_page(page_id, is_database=is_database, page_info=page_info, recursive_depth=recursive_depth)

    def save_relation_and_process_bookmark(self, parent_id: str, url: str, rel_type: RelationType = RelationType.REFERENCES,
                                           rel_context: str = None, recursive_depth: int = 0):
        self.page_relations.append(NotionRelation(parent_id, rel_type, url, rel_context))
        self.process_unprocessed_bookmark(url, recursive_depth=recursive_depth)

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
            self.save_relation_and_process_page(
                parent_id=parent_id,
                rel_type=RelationType.CONTAINS,
                page_id=block['id'],
                is_database=block['type'] == 'child_database',
                recursive_depth=recursive_depth)

        elif block['type'] == 'link_to_page':
            uuid = block['link_to_page'][block['link_to_page']['type']]
            self.save_relation_and_process_page(
                parent_id=parent_id,
                rel_type=RelationType.REFERENCES,
                page_id=uuid,
                recursive_depth=recursive_depth)

        elif block['type'] in rich_text_block_types:
            self.process_rich_text_array(block[block['type']]['rich_text'], parent_id, recursive_depth)

        elif block['type'] in url_block_types:
            # TODO parse mentions in captions (where supported)
            url = block[block['type']]['url']
            self.save_relation_and_process_bookmark(
                parent_id=parent_id,
                url=url,
                recursive_depth=recursive_depth
            )

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

    def process_rich_text_array(self, rich_text_array: list, parent_id: str, recursive_depth: int, rel_context: str = None):
        for text in rich_text_array:
            if 'href' in text and text['href']:
                uuid = _extract_notion_uuid(text['href'])
                full_context = f"{rel_context}\n{_extract_rich_text(rich_text_array)}" if rel_context else _extract_rich_text(rich_text_array)
                if uuid:
                    self.save_relation_and_process_page(
                        parent_id=parent_id,
                        rel_type=RelationType.REFERENCES,
                        page_id=uuid,
                        rel_context=full_context,
                        recursive_depth=recursive_depth
                    )
                else:
                    self.save_relation_and_process_bookmark(
                        parent_id=parent_id,
                        url=text['href'],
                        rel_context=full_context,
                        recursive_depth=recursive_depth
                    )

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
                logger.error(f"[Depth={recursive_depth}] Failed to get page info for page: {page_id}: {e}")
                logger.debug(f"Stack_trace for {page_id} exception", stack_info=True, stacklevel=15)
                return

        # TODO don't save page only if already exists in neo4j and last_edited_time is not greater than in neo4j
        page = NotionPage(page_id, _extract_title(page_info), get_page_type_from_string(page_info['object']), page_info['url'], last_edited_time=page_info['last_edited_time'])
        logger.info(f"[Depth={recursive_depth}] Adding new processed page[{len(self.prepared_pages)}]: {page.title}({page.type};{page.id})")
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

    def recursive_process_page_properties(self, page_info: dict, recursive_depth: int = 0):
        unsupported_properties = [
            'checkbox',
            'created_by',
            'created_time',
            'date',
            'email',
            'formula',
            'last_edited_by',
            'last_edited_time',
            'multi_select',
            'number',
            'people', # add support later
            'phone_number',
            'rollup',
            'select',
            'status',
            'unique_id',
            'verification',
        ]

        for prop_name in page_info['properties']:
            prop = page_info['properties'][prop_name]
            if prop['type'] == 'files' and prop['files']:
                # TODO for every file extract ['external']['url']
                pass
            if prop['type'] == 'relation' and prop['relation']:
                relations = self.get_paginated_properties(page_info['id'], prop, 'relation')
                for relation in relations:
                    self.save_relation_and_process_page(
                        parent_id=page_info['id'],
                        rel_type=RelationType.REFERENCES,
                        page_id=relation['id'],
                        rel_context=f"Page property {prop_name}",
                        recursive_depth=recursive_depth
                    )
            if prop['type'] == 'rich_text' and prop['rich_text']:
                rich_text_array = self.get_paginated_properties(page_info['id'], prop, 'rich_text')
                self.process_rich_text_array(rich_text_array, page_info['id'], rel_context=f"Page property {prop_name}", recursive_depth=recursive_depth)
            if prop['type'] == 'title' and prop['title']:
                rich_text_array = self.get_paginated_properties(page_info['id'], prop, 'title')
                self.process_rich_text_array(rich_text_array, page_info['id'], rel_context=f"Page property {prop_name}", recursive_depth=recursive_depth)
            if prop['type'] == 'url' and prop['url']:
                self.save_relation_and_process_bookmark(
                    parent_id=page_info['id'],
                    url=prop['url'],
                    rel_context=f"Page property {prop_name}",
                    recursive_depth=recursive_depth
                )

    def get_paginated_properties(self, page_id: str, prop: dict, prop_name: str):
        return [elem[prop_name] for elem in self.notion_api.get_all_page_properties(page_id, prop['id'])] if 'has_more' in prop and prop['has_more'] else prop[prop_name]