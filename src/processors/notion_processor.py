from src.data_sources.notion_api import NotionAPI

class NotionProcessor:
    def __init__(self):
        self.notion_api = NotionAPI()

    def process_page(self, page_id):
        page_content = self.notion_api.get_page_content(page_id)

        title = self._extract_title(page_content)
        content = self._extract_full_content(page_id)

        return {
            "page_id": page_id,
            "title": title,
            "content": content
        }

    def _extract_title(self, page_content):
        return page_content['properties']['title']['title'][0]['plain_text']

    def _extract_full_content(self, page_id):
        content = ""
        blocks = self.notion_api.get_block_children(page_id)['results']

        for block in blocks:
            content += self._process_block(block)

        return content

    def _process_block(self, block):
        content = ""
        if block['type'] == 'paragraph':
            content += self._extract_rich_text(block['paragraph']['rich_text'])
        elif block['type'].startswith('heading_'):
            content += self._extract_rich_text(block[block['type']]['rich_text'])
        elif block['type'] == 'bulleted_list_item':
            content += "• " + self._extract_rich_text(block['bulleted_list_item']['rich_text'])
        elif block['type'] == 'numbered_list_item':
            content += "1. " + self._extract_rich_text(block['numbered_list_item']['rich_text'])

        content += "\n"

        if 'has_children' in block and block['has_children']:
            child_blocks = self.notion_api.get_block_children(block['id'])['results']
            for child_block in child_blocks:
                content += self._process_block(child_block)

        return content

    def _extract_rich_text(self, rich_text):
        return ''.join([text['plain_text'] for text in rich_text])
