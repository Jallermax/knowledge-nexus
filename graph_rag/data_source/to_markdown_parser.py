import logging
from datetime import datetime

from graph_rag.config import Config

logger = logging.getLogger(__name__)


class Notion2MarkdownParser:
    def __init__(self):
        self.config = Config()
        self.indent = self.config.NOTION_MARKDOWN_INDENT
        self.property_handlers = {
            "checkbox": self._handle_checkbox,
            "created_by": self._handle_created_by,
            "created_time": self._handle_created_time,
            "date": self._handle_date,
            "email": self._handle_email,
            "files": self._handle_files,
            "formula": self._handle_formula,
            "last_edited_by": self._handle_last_edited_by,
            "last_edited_time": self._handle_last_edited_time,
            "multi_select": self._handle_multi_select,
            "number": self._handle_number,
            "people": self._handle_people,
            "phone_number": self._handle_phone_number,
            "relation": self._handle_relation,
            "rollup": self._handle_rollup,
            "rich_text": self._handle_rich_text,
            "select": self._handle_select,
            "status": self._handle_status,
            "title": self._handle_title,
            "url": self._handle_url,
            "unique_id": self._handle_unique_id,
            "verification": self._handle_verification
        }
        for property_type in self.config.NOTION_MARKDOWN_PARSER_EXCLUDED_PROPERTY_TYPES:
            self.property_handlers.pop(property_type, '')

        self.block_handlers = {
            "paragraph": self._handle_paragraph,
            "heading_1": self._handle_heading,
            "heading_2": self._handle_heading,
            "heading_3": self._handle_heading,
            "bulleted_list_item": self._handle_bulleted_list_item,
            "numbered_list_item": self._handle_numbered_list_item,
            "to_do": self._handle_to_do,
            "toggle": self._handle_toggle,
            "code": self._handle_code,
            "quote": self._handle_quote,
            "callout": self._handle_callout,
            "child_database": self._handle_child_database,
            "child_page": self._handle_child_page,
            "bookmark": self._handle_bookmark,
            "image": self._handle_image,
            "divider": self._handle_divider,
            "breadcrumb": self._handle_breadcrumb,
            "column_list": self._handle_column_list,
            "column": self._handle_column,
            "embed": self._handle_embed,
            "equation": self._handle_equation,
            "file": self._handle_file,
            "link_preview": self._handle_link_preview,
            "link_to_page": self._handle_link_to_page,
            "pdf": self._handle_pdf,
            "synced_block": self._handle_synced_block,
            "table": self._handle_table,
            "table_row": self._handle_table_row,
            "table_of_contents": self._handle_table_of_contents,
            "template": self._handle_template,
            "video": self._handle_video,
        }
        for block_type in self.config.NOTION_MARKDOWN_PARSER_EXCLUDED_BLOCK_TYPES:
            self.block_handlers.pop(block_type, '')

    def parse_properties(self, properties: dict) -> str:
        markdown = ""
        for prop_name, prop in properties.items():
            prop_type = prop['type']
            if prop_type in self.property_handlers:
                if prop[prop_type]:
                    markdown += f"**{prop_name}**: {self.property_handlers[prop_type](prop[prop_type])}\n"
            elif prop_type not in self.config.NOTION_MARKDOWN_PARSER_EXCLUDED_PROPERTY_TYPES:
                logger.warning(f"Unsupported property type: {prop_type}")
        return f"###Properties:\n{markdown}" if markdown else ''

    def parse_block(self, block: dict, indent_level: int = 0) -> str:
        block_type = block['type']
        if block_type in self.block_handlers:
            return self.block_handlers[block_type](block, (self.indent * indent_level))
        elif block_type not in self.config.NOTION_MARKDOWN_PARSER_EXCLUDED_BLOCK_TYPES:
            logger.warning(f"Unsupported block type: {block_type}")
            return ""

    @staticmethod
    def _handle_checkbox(value: bool) -> str:
        return "✅" if value else "❌"

    @staticmethod
    def _handle_created_by(value: dict) -> str:
        return f"Created by {value.get('name', 'Unknown')}"

    @staticmethod
    def _handle_created_time(value: str) -> str:
        return _format_date(value)

    @staticmethod
    def _handle_date(value: dict) -> str:
        start = value.get('start')
        end = value.get('end')
        if end:
            return f"{_format_date(start)} - {_format_date(end)}"
        return _format_date(start)

    @staticmethod
    def _handle_email(value: str) -> str:
        return value

    @staticmethod
    def _handle_files(value: list[dict]) -> str:
        return ", ".join([f"[{file.get('name', 'Unnamed')}]({file[file['type']]['url']})" for file in value])

    @staticmethod
    def _handle_formula(value: dict) -> str:
        return str(value.get(value['type'], 'N/A'))

    @staticmethod
    def _handle_last_edited_by(value: dict) -> str:
        return f"Last edited by {value.get('name', 'Unknown')}"

    @staticmethod
    def _handle_last_edited_time(value: str) -> str:
        return _format_date(value)

    @staticmethod
    def _handle_multi_select(value: list[dict]) -> str:
        return " ".join([Notion2MarkdownParser._handle_select(option) for option in value])

    @staticmethod
    def _handle_number(value: float) -> str:
        return str(value)

    @staticmethod
    def _handle_people(value: list[dict]) -> str:
        return ", ".join([person.get('name', 'Unknown') for person in value])

    @staticmethod
    def _handle_phone_number(value: str) -> str:
        return value

    @staticmethod
    def _handle_relation(value: list[dict]) -> str:
        return ", ".join([f"[Related Page]({page['id']})" for page in value])

    @staticmethod
    def _handle_rollup(value: dict) -> str:
        return f"{value['function']}: {value.get(value['type'], 'N/A')}"

    @staticmethod
    def _handle_rich_text(value: list[dict]) -> str:
        return _extract_rich_text(value)

    @staticmethod
    def _handle_select(value: dict) -> str:
        name = value.get('name')
        return f"#{name}" if name else ''

    @staticmethod
    def _handle_status(value: dict) -> str:
        return value.get('name', 'N/A')

    @staticmethod
    def _handle_title(value: list[dict]) -> str:
        return _extract_rich_text(value)

    @staticmethod
    def _handle_url(value: str) -> str:
        return f"[{value}]({value})"

    @staticmethod
    def _handle_unique_id(value: dict) -> str:
        prefix = value.get('prefix', '')
        return f"{prefix}{value['number']}"

    @staticmethod
    def _handle_verification(value: dict) -> str:
        state = value['state']
        if state == 'verified':
            verified_by = value['verified_by'].get('name', 'Unknown') if value['verified_by'] else 'Unknown'
            date = Notion2MarkdownParser._handle_date(value['date']) if value['date'] else 'N/A'
            return f"Verified by {verified_by} on {date}"
        return "Unverified"

    # Block processing methods
    @staticmethod
    def _handle_paragraph(block: dict, indent: str) -> str:
        return f"{indent}{_extract_rich_text(block['paragraph']['rich_text'])}\n\n"

    @staticmethod
    def _handle_heading(block: dict, indent: str) -> str:
        level = int(block['type'][-1])
        return f"{indent}{'#' * level} {_extract_rich_text(block[block['type']]['rich_text'])}\n\n"

    @staticmethod
    def _handle_bulleted_list_item(block: dict, indent: str) -> str:
        return f"{indent}- {_extract_rich_text(block['bulleted_list_item']['rich_text'])}\n"

    @staticmethod
    def _handle_numbered_list_item(block: dict, indent: str) -> str:
        return f"{indent}1. {_extract_rich_text(block['numbered_list_item']['rich_text'])}\n"

    @staticmethod
    def _handle_to_do(block: dict, indent: str) -> str:
        checkbox = "x" if block['to_do']['checked'] else " "
        return f"{indent}- [{checkbox}] {_extract_rich_text(block['to_do']['rich_text'])}\n"

    @staticmethod
    def _handle_toggle(block: dict, indent: str) -> str:
        summary = _extract_rich_text(block['toggle']['rich_text'])
        return f"{indent}<details>\n{indent}<summary>{summary}</summary>\n{indent}<details>\n\n"

    @staticmethod
    def _handle_code(block: dict, indent: str) -> str:
        language = block['code']['language']
        code = _extract_rich_text(block['code']['rich_text'])
        return f"{indent}```{language}\n{code}\n{indent}```\n\n"

    @staticmethod
    def _handle_quote(block: dict, indent: str) -> str:
        return f"{indent}> {_extract_rich_text(block['quote']['rich_text'])}\n\n"

    @staticmethod
    def _handle_callout(block: dict, indent: str) -> str:
        icon = block['callout']['icon']
        icon_string = f" :{icon['emoji']}:" if icon and icon.get('emoji') else ''
        text = _extract_rich_text(block['callout']['rich_text'])
        return f"{indent}>{icon_string} {text}\n\n"

    @staticmethod
    def _handle_child_database(block: dict, indent: str) -> str:
        title = block['child_database'].get('title', '')
        return f"{indent}Child database: {title}\n\n"

    @staticmethod
    def _handle_child_page(block: dict, indent: str) -> str:
        title = block['child_page'].get('title', '')
        return f"{indent}Child page: {title}\n\n"

    @staticmethod
    def _handle_bookmark(block: dict, indent: str) -> str:
        url = block['bookmark']['url']
        caption = _extract_rich_text(block['bookmark'].get('caption', []))
        return f"{indent}[{caption or 'Bookmark'}]({url})\n\n"

    @staticmethod
    def _handle_image(block: dict, indent: str) -> str:
        caption = _extract_rich_text(block['image'].get('caption', []))
        url = block['image']['file']['url'] if block['image']['type'] == 'file' else block['image']['external']['url']
        return f"{indent}![{caption}]({url})\n\n"

    @staticmethod
    def _handle_divider(_block: dict, indent: str) -> str:
        return f"{indent}---\n\n"

    @staticmethod
    def _handle_breadcrumb(_block: dict, indent: str) -> str:
        return f"{indent}[Breadcrumb]\n\n"

    @staticmethod
    def _handle_column_list(_block: dict, indent: str) -> str:
        return f"{indent}[Column list Start]\n\n"

    @staticmethod
    def _handle_column(_block: dict, indent: str) -> str:
        return f"{indent}[Column Start]\n\n"

    @staticmethod
    def _handle_embed(block: dict, indent: str) -> str:
        url = block['embed']['url']
        return f"{indent}[Embed: {url}]\n\n"

    @staticmethod
    def _handle_equation(block: dict, indent: str) -> str:
        expression = block['equation']['expression']
        return f"{indent}$$\n{expression}\n$$\n\n"

    @staticmethod
    def _handle_file(block: dict, indent: str) -> str:
        file_info = block['file']
        caption = _extract_rich_text(file_info.get('caption', []))
        url = file_info[file_info['type']]['url']
        name = file_info.get('name', '')
        return f"{indent}[File: [{name or caption or 'File'}]({url}){' - ' + caption if caption else ''}]\n\n"

    @staticmethod
    def _handle_link_preview(block: dict, indent: str) -> str:
        url = block['link_preview']['url']
        return f"{indent}[Link Preview: {url}]\n\n"

    @staticmethod
    def _handle_link_to_page(block: dict, indent: str) -> str:
        uuid = block['link_to_page'][block['link_to_page']['type']].replace('-', '')
        return f"{indent}[Link to page: {uuid}]\n\n"

    @staticmethod
    def _handle_pdf(block: dict, indent: str) -> str:
        pdf_info = block['pdf']
        caption = _extract_rich_text(pdf_info.get('caption', []))
        url = pdf_info[pdf_info['type']]['url']
        return f"{indent}[PDF]({url}){' - ' + caption if caption else ''}]\n\n"

    @staticmethod
    def _handle_synced_block(block: dict, indent: str) -> str:
        if block['synced_block']['synced_from'] is None:
            return f"{indent}[Original Synced Block]\n\n"
        else:
            original_block_id = block['synced_block']['synced_from']['block_id']
            return f"{indent}[Synced Block: Original ID {original_block_id}]\n\n"

    @staticmethod
    def _handle_table(block: dict, indent: str) -> str:
        table_info = block['table']
        width = table_info['table_width']
        has_column_header = table_info['has_column_header']
        has_row_header = table_info['has_row_header']
        return f"{indent}[Table: {width} columns, Column Header: {has_column_header}, Row Header: {has_row_header}]\n\n"

    @staticmethod
    def _handle_table_row(block: dict, indent: str) -> str:
        cells = block['table_row']['cells']
        row_content = " | ".join([_extract_rich_text(cell) for cell in cells])
        return f"{indent}| {row_content} |\n"

    @staticmethod
    def _handle_table_of_contents(_block: dict, indent: str) -> str:
        return f"{indent}[Table of Contents]\n\n"

    @staticmethod
    def _handle_template(block: dict, indent: str) -> str:
        template_text = _extract_rich_text(block['template']['rich_text'])
        return f"{indent}[Template: {template_text}]\n\n"

    @staticmethod
    def _handle_video(block: dict, indent: str) -> str:
        video_info = block['video']
        caption = _extract_rich_text(video_info.get('caption', []))
        url = video_info[video_info['type']]['url']
        return f"{indent}[Video: {url}{' - ' + caption if caption else ''}]\n\n"

    # Helper methods


def _extract_rich_text(rich_text: list[dict]) -> str:
    text = ""
    for rt in rich_text:
        content = rt['plain_text']
        annotations = rt['annotations']

        if annotations['code']:
            content = f"`{content}`"
        if annotations['bold']:
            content = f"**{content}**"
        if annotations['italic']:
            content = f"*{content}*"
        if annotations['strikethrough']:
            content = f"~~{content}~~"
        if annotations['underline']:
            content = f"<u>{content}</u>"

        if rt['type'] == 'text' and rt['text'].get('link'):
            content = f"[{content}]({rt['text']['link']['url']})"
        elif rt.get('href'):
            content = f"[{content}]({rt['href']})"

        if annotations['color'] != 'default':
            content = f'<span style="color: {annotations["color"].replace("_background", "")}">{content}</span>'

        text += content
    return text


def _format_date(date_string: str) -> str:
    try:
        date = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        return date.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return date_string
