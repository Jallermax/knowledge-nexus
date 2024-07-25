import os
import pickle
import time
from datetime import timedelta
from typing import Dict, Any, Type

from graph_rag.config.config_manager import Config
from graph_rag.data_model.cacheable import Cacheable

config = Config()


def save_cache(file_path: str, data: Dict[str, Any]):
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)


def load_cache(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def save_model_cache(file_name: str, model_data: Any, model_class: Type[Cacheable], key: str):
    file_path = os.path.join(config.CACHE_PATH, file_name)
    cache_data = {
        'version': model_class.get_class_version(),
        'key': key,
        'save_time': time.time(),
        'data': model_data
    }
    save_cache(file_path, cache_data)


def load_model_cache(file_name: str, model_class: Type[Cacheable], key: str) -> Any:
    file_path = os.path.join(config.CACHE_PATH, file_name)
    cache_data = load_cache(file_path)
    model_class.check_version(cache_data['version'])
    if cache_data['key'] != key:
        raise ValueError(f"Cache key mismatch: expected {key}, got {cache_data['key']}")
    if (time.time() - cache_data.get('save_time', 0)) > timedelta(seconds=config.CACHE_TTL_SECONDS).total_seconds():
        raise ValueError("Cache expired")
    return cache_data['data']
