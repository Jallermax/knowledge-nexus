import pickle
from typing import Dict, Any, Type

from graph_rag.data_model.cacheable import Cacheable


def save_cache(file_path: str, data: Dict[str, Any]):
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)


def load_cache(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def save_model_cache(file_path: str, model_data: Any, model_class: Type[Cacheable], key: str):
    cache_data = {
        'version': model_class.get_class_version(),
        'key': key,
        'data': model_data
    }
    save_cache(file_path, cache_data)


def load_model_cache(file_path: str, model_class: Type[Cacheable], key: str) -> Any:
    cache_data = load_cache(file_path)
    model_class.check_version(cache_data['version'])
    if cache_data['key'] != key:
        raise ValueError(f"Cache key mismatch: expected {key}, got {cache_data['key']}")
    return cache_data['data']
