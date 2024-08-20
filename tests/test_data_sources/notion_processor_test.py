import unittest
from unittest.mock import patch, MagicMock

from graph_rag.data_model.graph_data_classes import GraphPage, GraphRelation, RelationType, PageType
from graph_rag.data_source.notion_provider import (NotionProvider,
                                                   _extract_notion_uuid,
                                                   normalize_uuid,
                                                   _extract_title,
                                                   _extract_rich_text,
                                                   first_time_after_second)


class TestNotionProvider(unittest.TestCase):

    def setUp(self):
        # Create a mock for NotionAPI, Config, and Notion2MarkdownParser
        self.mock_notion_api = patch('graph_rag.data_source.notion_api.NotionAPI').start()
        self.mock_config = patch('graph_rag.config.config_manager.Config').start()
        self.mock_parser = patch('graph_rag.data_source.to_markdown_parser.Notion2MarkdownParser').start()

        self.mock_notion_api.return_value = MagicMock()
        self.mock_config.return_value = MagicMock()
        self.mock_parser.return_value = MagicMock()

        # Initialize the NotionProvider with mocked dependencies
        self.processor = NotionProvider()

    def tearDown(self):
        patch.stopall()

    def test_extract_notion_uuid(self):
        href = "https://www.notion.so/username/Some-Page-bf98f999-c90a-41e1-98f9-99c90a01e1d2"
        expected_uuid = "bf98f999c90a41e198f999c90a01e1d2"
        self.assertEqual(_extract_notion_uuid(href), expected_uuid)

        href_invalid = "https://www.example.com"
        self.assertIsNone(_extract_notion_uuid(href_invalid))

    def test_normalize_uuid(self):
        uuid_with_dashes = "bf98f999-c90a-41e1-98f9-99c90a01e1d2"
        normalized_uuid = "bf98f999c90a41e198f999c90a01e1d2"
        self.assertEqual(normalize_uuid(uuid_with_dashes), normalized_uuid)

        uuid_without_dashes = "bf98f999c90a41e198f999c90a01e1d2"
        self.assertEqual(normalize_uuid(uuid_without_dashes), uuid_without_dashes)

    def test_extract_title(self):
        page_content = {
            'title': [{'plain_text': 'Test Title'}],
            'properties': {
                'Name': {'type': 'title', 'title': [{'plain_text': 'Property Title'}]}
            }
        }
        self.assertEqual(_extract_title(page_content), 'Test Title')

        page_content_no_title = {
            'properties': {
                'Name': {'type': 'title', 'title': [{'plain_text': 'Property Title'}]}
            }
        }
        self.assertEqual(_extract_title(page_content_no_title), 'Property Title')

        page_content_empty = {
            'properties': {}
        }
        self.assertEqual(_extract_title(page_content_empty), 'Untitled')

    def test_extract_rich_text(self):
        rich_text = [
            {'plain_text': 'This '},
            {'plain_text': 'is '},
            {'plain_text': 'a '},
            {'plain_text': 'test.'}
        ]
        self.assertEqual(_extract_rich_text(rich_text), 'This is a test.')

    def test_first_time_after_second(self):
        time1 = "2023-08-01T12:00:00.000Z"
        time2 = "2023-08-01T11:00:00.000Z"
        self.assertTrue(first_time_after_second(time1, time2))

        time3 = "2023-08-01T10:00:00.000Z"
        self.assertFalse(first_time_after_second(time3, time2))

    @patch('graph_rag.utils.cache_util.load_prepared_pages_from_cache')
    @patch('graph_rag.utils.cache_util.load_page_relations_from_cache')
    def test_process_pages_with_cache(self, mock_load_pages, mock_load_relations):
        # Setup
        mock_load_pages.return_value = {
            "page_id": GraphPage(id="page_id", title="Test Page", type=PageType.PAGE, url="url")}
        mock_load_relations.return_value = [
            GraphRelation(from_page_id="page_id", relation_type=RelationType.CONTAINS, to_page_id="child_page_id")]

        self.processor.config.CACHE_ENABLED = True

        # Execution
        self.processor.process_pages("root_page_id")

        # Assertions
        self.assertEqual(len(self.processor.prepared_pages), 1)
        self.assertEqual(len(self.processor.page_relations), 1)
        mock_load_pages.assert_called_once_with("root_page_id")
        mock_load_relations.assert_called_once_with("root_page_id")
