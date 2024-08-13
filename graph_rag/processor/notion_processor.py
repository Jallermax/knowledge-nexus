import logging
import os
import re
from datetime import datetime

from graph_rag.config.config_manager import Config
from graph_rag.data_model.graph_data_classes import GraphPage, get_page_type_from_string, GraphRelation, RelationType, \
    PageType, ProcessedData
from graph_rag.data_source.base_content_provider import ContentProvider
from graph_rag.data_source.notion_api import NotionAPI
from graph_rag.data_source.web_scraper import get_info_from_url
from graph_rag.processor.to_markdown_parser import Notion2MarkdownParser
from graph_rag.utils import cache_util

logger = logging.getLogger(__name__)


def _extract_notion_uuid(href):
    pattern = r"(https:\/\/www\.notion\.so)?/([a-zA-Z0-9\-]+/)?([a-zA-Z0-9\-]+-)?([a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12})(\?[a-zA-Z0-9%=\-&]*)?"
    match = re.match(pattern, href)
    if match:
        return match.group(4).replace('-', '')  # return the UUID

    else:
        return None  # return None if the href does not match the pattern


def normalize_uuid(uuid: str):
    return uuid.replace('-', '') if re.match(r'^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', uuid) else uuid


def _extract_title(page_content: dict):
    if 'title' in page_content and page_content['title']:
        return page_content['title'][0]['plain_text']
    else:
        for prop_name in page_content['properties']:
            prop = page_content['properties'][prop_name]
            if prop['type'] == 'title' and 'title' in prop and prop['title']:
                return prop['title'][0]['plain_text']
        return 'Untitled'


def _extract_rich_text(rich_text: list[dict]):
    return ''.join([text['plain_text'] for text in rich_text])


def first_time_after_second(first_time: str, second_time: str):
    dt_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    dt1 = datetime.strptime(first_time, dt_format)
    dt2 = datetime.strptime(second_time, dt_format)
    return dt1 > dt2


class NotionProcessor(ContentProvider):
    def __init__(self):
        super().__init__()
        self.notion_api = NotionAPI()
        self.config = Config()
        self.content_parser = Notion2MarkdownParser()
        self.prepared_pages: dict[str, GraphPage] = {}
        self.page_relations: list[GraphRelation] = []
        os.makedirs(self.config.CACHE_PATH, exist_ok=True)
        logger.info("NotionProcessor initialized")

    def fetch_data(self) -> ProcessedData:
        self.process_pages(self.config.NOTION_ROOT_PAGE_ID)

        logger.info(f"Prepared {len(self.prepared_pages)} pages from Notion")
        logger.info(f"Prepared {len(self.page_relations)} relations from Notion")

        return ProcessedData(self.prepared_pages, self.page_relations)

    def process_pages(self, root_page_id: str):
        if self.config.CACHE_ENABLED:
            try:
                self.prepared_pages = cache_util.load_prepared_pages_from_cache(root_page_id)
                self.page_relations = cache_util.load_page_relations_from_cache(root_page_id)
                logger.info(f"Loaded from cache: {len(self.prepared_pages)} pages and {len(self.page_relations)} relations")
                # self.refresh_updated_pages()
                # cache_util.save_prepared_pages_to_cache(root_page_id, self.prepared_pages)
                # cache_util.save_page_relations_to_cache(root_page_id, self.page_relations)
                logger.info("Cache updated with the latest changes")
                return
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}. Running the ingestion process.")

        logger.info(f"Processing root page: {root_page_id}")
        root_page = self.notion_api.get_root_page_info(root_page_id)
        notion_page = GraphPage(normalize_uuid(root_page['id']), _extract_title(root_page),
                                get_page_type_from_string(root_page['object']),
                                root_page['url'], source='Notion', last_edited_time=root_page['last_edited_time'])
        self.prepared_pages.update({notion_page.id: notion_page})
        notion_page.content = self.recursive_process_page_content(root_page)

        if self.config.CACHE_ENABLED:
            cache_util.save_prepared_pages_to_cache(root_page_id, self.prepared_pages)
            cache_util.save_page_relations_to_cache(root_page_id, self.page_relations)
            logger.info("Saved processed notion data to cache.")

    def refresh_updated_pages(self):
        logger.info("Refreshing processed pages with the latest changes")
        for i, page in enumerate(self.prepared_pages.values()):
            if page.type != PageType.BOOKMARK:
                logger.info(f"Checking page {i}/{len(self.prepared_pages)}: {page.title}-{page.id}")
                self.recursive_process_unprocessed_page(page.id, page.type == PageType.DATABASE)

    def recursive_process_page_content(self, page_info: dict, recursive_depth: int = 0) -> str | None:
        """
        Recursively process all blocks of the given page and its sub-pages if this page hasn't been processed before
        (not in self.processed_pages). Add every processed sub-page into processed_pages and add relation to
        page_relations If is_database, then make additional call of get_all_database_items to get all db pages
        """
        recursive_depth += 1
        if recursive_depth >= self.config.NOTION_PAGE_MAX_DEPTH:
            logger.warning(
                f"Current recursion depth {recursive_depth} for processing pages exceeded depth limit. See "
                f"notion_api.page_max_depth in config.yaml")
            return None
        is_database = page_info['object'] == 'database'
        logger.debug(f"[Depth={recursive_depth}] Recursively processing page: {page_info['id']}, is_database: {is_database}")

        content = ''
        # TODO add parse comments
        if is_database:
            # TODO parse mentions in db title and relations in db properties
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
            content = self.content_parser.parse_properties(page_info['properties'])

        try:
            child_blocks = self.notion_api.get_all_content_blocks(page_info['id'])
        except Exception as e:
            logger.error(f"[Depth={recursive_depth}] Exception occurred during fetching of page {page_info['id']} blocks: {e}")
            logger.debug(f"Stack_trace for {page_info['id']} exception", stack_info=True, stacklevel=15)
            return content
        for block in child_blocks:
            content += self.recursive_process_block(block, parent_id=page_info['id'], recursive_depth=recursive_depth)

        return content

    def save_relation_and_process_page(self, parent_id: str, rel_type: RelationType, page_id: str,
                                       rel_context: str = None,
                                       is_database: bool = None, page_info: dict = None, recursive_depth: int = 0):
        self.page_relations.append(GraphRelation(normalize_uuid(parent_id), rel_type, normalize_uuid(page_id), rel_context))
        if rel_type == RelationType.REFERENCES and not self.config.NOTION_RECURSIVE_PROCESS_REFERENCE_PAGES:
            return
        self.recursive_process_unprocessed_page(page_id, is_database=is_database, page_info=page_info,
                                                recursive_depth=recursive_depth)

    def save_relation_and_process_bookmark(self, parent_id: str, url: str,
                                           rel_type: RelationType = RelationType.REFERENCES,
                                           rel_context: str = None, recursive_depth: int = 0):
        self.page_relations.append(GraphRelation(normalize_uuid(parent_id), rel_type, url, rel_context))
        self.process_unprocessed_bookmark(url, recursive_depth=recursive_depth)

    def recursive_process_block(self, block: dict, parent_id: str, indent_level: int = 0,
                                recursive_depth: int = 0) -> str:
        logger.debug(f"[Depth={recursive_depth}] Recursively parsing block: {block['id']}, parent_id: {parent_id}")
        unsupported_block_types = [
            'breadcrumb',
            'column',  # retrieve block children for content
            'column_list',  # retrieve block children for columns
            'divider',
            'equation',
            'file',  # TODO parse caption
            'image',
            'pdf',  # TODO parse caption
            'synced_block',
            'table',
            'table_row',
            'table_of_contents',
            'video',
        ]
        url_block_types = [
            'bookmark',  # TODO parse caption
            'embed',
            'link_preview',
        ]
        rich_text_block_types = [
            'bulleted_list_item',
            'callout',
            'code',  # TODO parse caption
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
            url = block[block['type']]['url']
            self.save_relation_and_process_bookmark(
                parent_id=parent_id,
                url=url,
                recursive_depth=recursive_depth
            )

        elif block['type'] == 'unsupported':
            logger.warning(f"Unsupported block_id {block['id']} of page {parent_id}")
            return ''

        block_content = self.content_parser.parse_block(block, indent_level)
        content = block_content if block_content else ''

        if 'has_children' in block and block['has_children'] and block['type'] not in ['child_page', 'child_database']:
            try:
                child_blocks = self.notion_api.get_all_content_blocks(block['id'])
            except Exception as e:
                logger.error(f"[Depth={recursive_depth}] Exception occurred during fetching of page {block['id']} blocks: {e}")
                logger.debug(f"Stack_trace for {block['id']} exception", stack_info=True, stacklevel=15)
                return content
            for child_block in child_blocks:
                content += self.recursive_process_block(child_block, parent_id, indent_level + 1, recursive_depth)

        return content

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
        if url not in self.prepared_pages.keys():
            try:
                title, description = get_info_from_url(url)
            except:
                title, description = '', ''
            bookmark_page = GraphPage(url, title, PageType.BOOKMARK, url, content=description, source='Web')
            logger.info(f"[Depth={recursive_depth}] Adding new processed bookmark[{len(self.prepared_pages)}]: [{title}]({url})")
            self.prepared_pages.update({url: bookmark_page})

    def recursive_process_unprocessed_page(self, page_id: str, is_database: bool = None, page_info: dict = None, recursive_depth: int = 0):
        page_id = normalize_uuid(page_id)

        if not page_info:
            try:
                if is_database is None:
                    page_info = self.notion_api.get_root_page_info(page_id)
                elif is_database:
                    page_info = self.notion_api.get_database_metadata(page_id)
                else:
                    page_info = self.notion_api.get_page_metadata(page_id)
            except Exception as e:
                logger.error(f"[Depth={recursive_depth}] Failed to get {'database' if is_database else 'page'} info for id: {page_id}: {e}")
                logger.debug(f"Stack_trace for {page_id} exception", stack_info=True, stacklevel=15)
                return

        # Stop processing if page already exists in prepared_pages and wasn't updated
        if page_id in self.prepared_pages.keys() and not first_time_after_second(page_info['last_edited_time'], self.prepared_pages[page_id].last_edited_time):
            return

        # TODO don't save page only if already exists in neo4j and last_edited_time is not greater than in neo4j
        page = GraphPage(page_id, _extract_title(page_info), get_page_type_from_string(page_info['object']),
                         page_info['url'], source='Notion', last_edited_time=page_info['last_edited_time'])

        if not self._should_add_page(page_info):
            return

        self._update_page_title(page_info, page)
        logger.info(f"[Depth={recursive_depth}] Adding new processed page[{len(self.prepared_pages)}]: {page.title}({page.type};{page.id})")
        self.prepared_pages.update({page_id: page})

        if not self._should_process_content(page_info):
            return

        page.content = self.recursive_process_page_content(page_info, recursive_depth=recursive_depth)

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
            'people',  # add support later
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
                        rel_context=f"Relation property **{prop_name}**",
                        recursive_depth=recursive_depth
                    )
            if prop['type'] == 'rich_text' and prop['rich_text']:
                rich_text_array = self.get_paginated_properties(page_info['id'], prop, 'rich_text')
                self.process_rich_text_array(rich_text_array, page_info['id'], rel_context=f"Text property **{prop_name}**:",
                                             recursive_depth=recursive_depth)
            if prop['type'] == 'title' and prop['title']:
                rich_text_array = self.get_paginated_properties(page_info['id'], prop, 'title')
                self.process_rich_text_array(rich_text_array, page_info['id'], rel_context=f"Title property **{prop_name}**:",
                                             recursive_depth=recursive_depth)
            if prop['type'] == 'url' and prop['url']:
                self.save_relation_and_process_bookmark(
                    parent_id=page_info['id'],
                    url=prop['url'],
                    rel_context=f"Url property **{prop_name}**",
                    recursive_depth=recursive_depth
                )

    def get_paginated_properties(self, page_id: str, prop: dict, prop_name: str):
        return [elem[prop_name] for elem in
                self.notion_api.get_all_page_properties(page_id, prop['id'])] if 'has_more' in prop and prop[
            'has_more'] else prop[prop_name]

    def _should_add_page(self, page_info: dict):
        if page_info['archived']:
            return self.config.NOTION_ADD_ARCHIVED_PAGE_NODES
        elif page_info['in_trash']:
            return self.config.NOTION_ADD_REMOVED_PAGE_NODES
        return True

    @staticmethod
    def _update_page_title(page_info: dict, page: GraphPage):
        if page_info['archived']:
            page.title = f"[ARCHIVED] {page.title}"
        elif page_info['in_trash']:
            page.title = f"[REMOVED] {page.title}"

    @staticmethod
    def _should_process_content(page_info: dict) -> bool:
        if page_info['archived'] or page_info['in_trash']:
            return False
        return True
