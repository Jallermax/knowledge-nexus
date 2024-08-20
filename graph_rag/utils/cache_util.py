import importlib
import json
import os
import time
from datetime import timedelta
from typing import Any, Type

from graph_rag.config import Config
from graph_rag.data_model import Cacheable
from graph_rag.data_model import GraphPage, GraphRelation

config = Config()


def get_all_cacheable_classes():
    cacheable_classes = {}
    for module_name in ['graph_rag.data_model.graph_data_classes']:  # Add more modules if needed
        module = importlib.import_module(module_name)
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, Cacheable) and obj != Cacheable:
                cacheable_classes[name] = obj
    return cacheable_classes


CACHEABLE_CLASSES = get_all_cacheable_classes()


def save_cache(file_path: str, data: dict[str, Any]):
    with open(file_path, 'w') as f:
        json.dump(data, f, default=custom_serializer)


def load_cache(file_path: str) -> dict[str, Any]:
    with open(file_path, 'r') as f:
        return json.load(f, object_hook=custom_deserializer)


def custom_serializer(obj):
    if isinstance(obj, Cacheable):
        return {
            '__cacheable__': True,
            'class': obj.__class__.__name__,
            'data': obj.to_dict()
        }
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')


def custom_deserializer(obj):
    if '__cacheable__' in obj:
        class_name = obj['class']
        if class_name in CACHEABLE_CLASSES:
            return CACHEABLE_CLASSES[class_name].from_dict(obj['data'])
    return obj


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


def save_prepared_pages_to_cache(root_page_id: str, prepared_pages: dict[str, GraphPage],
                                 file_name: str = 'prepared_pages.json'):
    save_model_cache(file_name,
                     {page_id: page.to_dict() for page_id, page in prepared_pages.items()}, GraphPage,
                     root_page_id)


def load_prepared_pages_from_cache(root_page_id: str, file_name: str = 'prepared_pages.json') -> dict[str, GraphPage]:
    prepared_pages_cache = load_model_cache(file_name, GraphPage, root_page_id)
    return {page_id: GraphPage.from_dict(page_data) for page_id, page_data
            in prepared_pages_cache.items()}


def save_page_relations_to_cache(root_page_id: str, page_relations: list[GraphRelation],
                                 file_name: str = 'page_relations.json'):
    save_model_cache(file_name,
                     [relation.to_dict() for relation in page_relations], GraphRelation, root_page_id)


def load_page_relations_from_cache(root_page_id: str, file_name: str = 'page_relations.json') -> list[GraphRelation]:
    page_relations_cache = load_model_cache(file_name, GraphRelation, root_page_id)
    return [GraphRelation.from_dict(relation_data) for relation_data
            in page_relations_cache]
