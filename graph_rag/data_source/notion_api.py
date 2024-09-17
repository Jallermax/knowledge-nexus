import hashlib
import json
import logging
import os
import time
from functools import wraps
from typing import Callable

import requests

from graph_rag.config import Config

logger = logging.getLogger(__name__)


def cache_api_call(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        cache_key = f"{func.__name__}:{args}:{kwargs}"

        # Check in-memory cache
        if cache_key in self.cache:
            cached_data, cache_time = self.cache[cache_key]
            if not self.cache_ttl or time.time() - cache_time < self.cache_ttl:
                return cached_data

        # If not in memory, check file cache
        if self.config.NOTION_CACHE_PATH:
            safe_filename = self._get_safe_filename(cache_key)
            cache_path = os.path.join(self.config.DATA_DIR, self.config.NOTION_CACHE_PATH)
            file_path = os.path.join(cache_path, safe_filename)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    file_cache = json.load(f)
                if not self.cache_ttl or time.time() - file_cache['time'] < self.cache_ttl:
                    self.cache[cache_key] = (file_cache['data'], file_cache['time'])
                    return file_cache['data']

        # If not in cache or expired, call the API
        result = func(self, *args, **kwargs)

        # Update in-memory cache
        self.cache[cache_key] = (result, time.time())

        # Update file cache
        if self.config.NOTION_CACHE_PATH:
            os.makedirs(cache_path, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump({'data': result, 'time': time.time()}, f)

        return result

    return wrapper


class NotionAPI:
    def __init__(self):
        self.config = Config()
        self.base_url = self.config.NOTION_API_BASE_URL
        self.version = self.config.NOTION_API_VERSION
        self.headers = {
            "Authorization": f"Bearer {self.config.NOTION_API_KEY}",
            "Notion-Version": self.version,
            "Content-Type": "application/json"
        }
        self.cache = {}
        self.cache_ttl = self.config.NOTION_CACHE_TTL_SECONDS

    @staticmethod
    def _get_safe_filename(cache_key: str) -> str:
        """Generate a safe filename from the cache key."""
        return hashlib.md5(cache_key.encode()).hexdigest() + '.json'

    @cache_api_call
    def get_page_metadata(self, page_id):
        url = f"{self.base_url}pages/{page_id}"
        response = requests.get(url, headers=self.headers, timeout=self.config.NOTION_API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch page info: {response.status_code} - {response.text}\nurl={url}")

    @cache_api_call
    def get_page_content_blocks(self, page_id, first_call=True, start_cursor=None, page_size=100):
        url = f"{self.base_url}blocks/{page_id}/children?page_size={page_size}"
        if start_cursor:
            url += "&start_cursor=" + start_cursor

        response = requests.get(url, headers=self.headers, timeout=self.config.NOTION_API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        elif 500 <= response.status_code < 600 and first_call:
            logger.info("Retrying failed request after 1 second...")
            time.sleep(1)
            return self.get_page_content_blocks(page_id, first_call=False, start_cursor=start_cursor,
                                                page_size=page_size)
        else:
            raise Exception(f"Failed to fetch block children: {response.status_code} - {response.text}\nurl={url}")

    def get_all_content_blocks(self, page_id):
        all_items = []
        has_more = True
        start_cursor = None

        while has_more:
            response = self.get_page_content_blocks(page_id, start_cursor=start_cursor)
            all_items.extend(response['results'])
            has_more = response['has_more']
            start_cursor = response.get('next_cursor')

        return all_items

    @cache_api_call
    def get_page_properties(self, page_id, property_id, first_call=True, start_cursor=None, page_size=100):
        url = f"{self.base_url}pages/{page_id}/properties/{property_id}?page_size={page_size}"
        if start_cursor:
            url += "&start_cursor=" + start_cursor

        response = requests.get(url, headers=self.headers, timeout=self.config.NOTION_API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        elif 500 <= response.status_code < 600 and first_call:
            logger.info("Retrying failed request after 1 second...")
            time.sleep(1)
            return self.get_page_properties(page_id, property_id, first_call=False, start_cursor=start_cursor,
                                            page_size=page_size)
        else:
            raise Exception(f"Failed to fetch page properties: {response.status_code} - {response.text}\nurl={url}")

    def get_all_page_properties(self, page_id, property_id):
        all_items = []
        has_more = True
        start_cursor = None

        while has_more:
            response = self.get_page_properties(page_id, property_id, start_cursor=start_cursor)
            all_items.extend(response['results'])
            has_more = response['has_more']
            start_cursor = response.get('next_cursor')

        return all_items

    @cache_api_call
    def get_database_metadata(self, database_id):
        url = f"{self.base_url}databases/{database_id}"
        response = requests.get(url, headers=self.headers, timeout=self.config.NOTION_API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch database info: {response.status_code} - {response.text}\nurl={url}")

    @cache_api_call
    def query_database(self, database_id, start_cursor=None, page_size=100):
        url = f"{self.base_url}databases/{database_id}/query"
        payload = {
            "page_size": page_size
        }
        if start_cursor:
            payload["start_cursor"] = start_cursor

        response = requests.post(url, headers=self.headers, json=payload, timeout=self.config.NOTION_API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to query database: {response.status_code} - {response.text}\nurl={url}")

    @cache_api_call
    def get_search_results(self, query: str = None, **search_filter) -> list[dict]:
        url = f"{self.base_url}search"
        params = {}
        if query:
            params["query"] = query
        if search_filter:
            params["filter"] = search_filter

        return self._get_all_paginated_results(url, **params)

    def _get_all_paginated_results(self, url, r_type=requests.api.post, page_size=100, **payload_params) -> list[dict]:
        logger.debug(f"Fetching paginated items from {url}(params: {payload_params})...")
        all_items = []
        has_more = True
        first_call = True
        payload = {
            "page_size": page_size,
            **payload_params
        }

        while has_more:
            response = r_type(url, headers=self.headers, timeout=self.config.NOTION_API_TIMEOUT, json=payload)
            if response.status_code == 200:
                response_json = response.json()
                all_items.extend(response_json['results'])
                has_more = response_json['has_more']
                payload.update({"start_cursor": response_json.get('next_cursor')})
                first_call = True
                logger.debug(
                    f"Retrieved {len(all_items)} paginated items.{' Fetching next page' if has_more else ' Finished.'}")
            elif 500 <= response.status_code < 600 and first_call:
                logger.info("Retrying failed request after 1 second...")
                first_call = False
                time.sleep(1)
            else:
                response.raise_for_status()

        return all_items

    def get_all_database_items(self, database_id):
        all_items = []
        has_more = True
        start_cursor = None

        while has_more:
            response = self.query_database(database_id, start_cursor)
            all_items.extend(response['results'])
            has_more = response['has_more']
            start_cursor = response.get('next_cursor')

        return all_items

    def get_root_page_info(self, root_id):
        try:
            return self.get_database_metadata(root_id)
        except Exception:
            return self.get_page_metadata(root_id)
