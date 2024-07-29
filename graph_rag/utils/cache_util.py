import os
import pickle
import time
from datetime import timedelta
from typing import Dict, Any, Type, List

from graph_rag.config.config_manager import Config
from graph_rag.data_model.cacheable import Cacheable
from graph_rag.data_model.notion_page import NotionPage, NotionRelation

config = Config()


def save_cache(file_path: str, data: Dict[str, Any]):
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)


def load_cache(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def save_model_cache(file_name: str, model_data: Any, model_class: Type[Cacheable], key: str):
    file_path = os.path.join(config.CACHE_PATH, file_name)
    # Load existing cache or create a new one
    try:
        cache_data = load_cache(file_path)
    except FileNotFoundError:
        cache_data = {}

    # Create a new entry for the current key
    cache_entry = {
        'version': model_class.get_class_version(),
        'save_time': time.time(),
        'data': model_data
    }

    # Add or update the entry for the given key
    cache_data[key] = cache_entry

    # Save the updated cache
    save_cache(file_path, cache_data)


def load_model_cache(file_name: str, model_class: Type[Cacheable], key: str) -> Any:
    file_path = os.path.join(config.CACHE_PATH, file_name)
    cache_data = load_cache(file_path)

    if key not in cache_data:
        raise KeyError(f"No cache entry found for key: {key}")

    cache_entry = cache_data[key]
    model_class.check_version(cache_entry['version'])

    if config.CACHE_TTL_SECONDS and (time.time() - cache_entry['save_time']) > timedelta(
            seconds=config.CACHE_TTL_SECONDS).total_seconds():
        raise ValueError("Cache expired")

    return cache_entry['data']


def show_saved_cache_info(file_name: str):
    file_path = os.path.join(config.CACHE_PATH, file_name)
    cache_data = load_cache(file_path)

    print(f"Cache file: {file_name}")
    for k, entry in cache_data.items():
        print(f"\nKey: {k}")
        print(f"Version: {entry['version']}")
        print(f"Save time: {time.ctime(entry['save_time'])}")
        print(f"Data size: {len(entry['data'])}")


def save_prepared_pages_to_cache(root_page_id: str, prepared_pages: Dict[str, NotionPage],
                                 file_name: str = 'prepared_pages.pkl'):
    save_model_cache(file_name,
                     {page_id: page.to_dict() for page_id, page in prepared_pages.items()}, NotionPage,
                     root_page_id)


def load_prepared_pages_from_cache(root_page_id: str, file_name: str = 'prepared_pages.pkl') -> Dict[str, NotionPage]:
    prepared_pages_cache = load_model_cache(file_name, NotionPage, root_page_id)
    return {page_id: NotionPage.from_dict(page_data) for page_id, page_data
            in prepared_pages_cache.items()}


def save_page_relations_to_cache(root_page_id: str, page_relations: List[NotionRelation],
                                 file_name: str = 'page_relations.pkl'):
    save_model_cache(file_name,
                     [relation.to_dict() for relation in page_relations], NotionRelation, root_page_id)


def load_page_relations_from_cache(root_page_id: str, file_name: str = 'page_relations.pkl') -> List[NotionRelation]:
    page_relations_cache = load_model_cache(file_name, NotionRelation, root_page_id)
    return [NotionRelation.from_dict(relation_data) for relation_data
            in page_relations_cache]
