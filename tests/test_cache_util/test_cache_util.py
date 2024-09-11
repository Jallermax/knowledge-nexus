import os
import tempfile
import time
import unittest
from dataclasses import dataclass
from unittest.mock import patch


class MockConfig:
    def __init__(self):
        self.DATA_DIR = 'data'
        self.CACHE_PATH = tempfile.mkdtemp()
        self.CACHE_TTL_SECONDS = 3600  # 1 hour


with patch('graph_rag.config.Config', MockConfig):
    from graph_rag.utils import cache_util
    from graph_rag.data_model import Cacheable, RelationType
    from graph_rag.data_model import GraphPage, GraphRelation, PageType


class TestCacheUtil(unittest.TestCase):
    def setUp(self):
        self.mock_config = MockConfig()
        self.patcher = patch('graph_rag.utils.cache_util.config', self.mock_config)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        path = os.path.join(self.mock_config.DATA_DIR, self.mock_config.CACHE_PATH)
        for file in os.listdir(path):
            os.remove(os.path.join(path, file))
        os.rmdir(path)

    def test_save_and_load_cache(self):
        file_path = os.path.join(self.mock_config.DATA_DIR, self.mock_config.CACHE_PATH, 'test_cache.pkl')
        data = {'key': 'value'}
        cache_util.save_cache(file_path, data)
        loaded_data = cache_util.load_cache(file_path)
        self.assertEqual(data, loaded_data)

    def test_save_and_load_model_cache(self):
        file_name = 'test_model_cache.pkl'
        key = 'test_key'

        @dataclass
        class TestModel(Cacheable):
            data: str

            @classmethod
            def get_class_version(cls):
                return 1

        model_data = TestModel('test_data')
        cache_util.save_model_cache(file_name, model_data.to_dict(), TestModel, key)
        loaded_data = cache_util.load_model_cache(file_name, TestModel, key)
        self.assertEqual(model_data.to_dict(), loaded_data)

    def test_version_mismatch(self):
        file_name = 'test_version_mismatch.pkl'
        key = 'test_key'

        @dataclass
        class OldModel(Cacheable):
            @classmethod
            def get_class_version(cls):
                return 1

        @dataclass
        class NewModel(Cacheable):
            @classmethod
            def get_class_version(cls):
                return 2

        cache_util.save_model_cache(file_name, {}, OldModel, key)
        with self.assertRaises(ValueError):
            cache_util.load_model_cache(file_name, NewModel, key)

    def test_cache_expiration(self):
        file_name = 'test_expiration.pkl'
        key = 'test_key'

        @dataclass
        class TestModel(Cacheable):
            @classmethod
            def get_class_version(cls):
                return 1

        self.mock_config.CACHE_TTL_SECONDS = 1  # Set TTL to 1 second for testing
        cache_util.save_model_cache(file_name, {}, TestModel, key)
        time.sleep(2)  # Wait for cache to expire
        with self.assertRaises(ValueError):
            cache_util.load_model_cache(file_name, TestModel, key)

    def test_save_and_load_prepared_pages(self):
        root_page_id = 'root_id'
        prepared_pages = {
            'page1': GraphPage('page1', 'Page 1', PageType.PAGE, 'http://test.com'),
            'page2': GraphPage('page2', 'Page 2', PageType.DATABASE, 'http://test.com/db')
        }
        cache_util.save_prepared_pages_to_cache(root_page_id, prepared_pages)
        loaded_pages = cache_util.load_prepared_pages_from_cache(root_page_id)
        self.assertEqual(len(prepared_pages), len(loaded_pages))
        for page_id, page in prepared_pages.items():
            self.assertEqual(page.to_dict(), loaded_pages[page_id].to_dict())

    def test_save_and_load_page_relations(self):
        root_page_id = 'root_id'
        page_relations = [
            GraphRelation('page1', RelationType.CONTAINS, 'page2'),
            GraphRelation('page2', RelationType.REFERENCES, 'page3')
        ]
        cache_util.save_page_relations_to_cache(root_page_id, page_relations)
        loaded_relations = cache_util.load_page_relations_from_cache(root_page_id)
        self.assertEqual(len(page_relations), len(loaded_relations))
        for i, relation in enumerate(page_relations):
            self.assertEqual(relation.to_dict(), loaded_relations[i].to_dict())

    def test_key_not_found(self):
        file_name = 'test_key_not_found.pkl'
        existing_key = 'existing_key'
        non_existent_key = 'non_existent_key'

        class TestModel(Cacheable):
            def __init__(self, data):
                self.data = data

            def to_dict(self):
                return {'data': self.data}

            @classmethod
            def from_dict(cls, data):
                return cls(data['data'])

            @classmethod
            def get_class_version(cls):
                return 1

        # First, save some data to the cache
        existing_data = TestModel('existing_data')
        cache_util.save_model_cache(file_name, existing_data.to_dict(), TestModel, existing_key)

        # Now try to load a non-existent key
        with self.assertRaises(KeyError):
            cache_util.load_model_cache(file_name, TestModel, non_existent_key)


if __name__ == '__main__':
    unittest.main()
