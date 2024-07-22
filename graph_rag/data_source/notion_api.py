import time

import requests
from graph_rag.config.config_manager import Config

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

    def get_page_metadata(self, page_id):
        url = f"{self.base_url}pages/{page_id}"
        response = requests.get(url, headers=self.headers, timeout=self.config.NOTION_API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch page info: {response.status_code} - {response.text}\nurl={url}")

    def get_page_content_blocks(self, page_id, first_call=True, start_cursor=None, page_size=100):
        url = f"{self.base_url}blocks/{page_id}/children?page_size={page_size}"
        if start_cursor:
            url += "&start_cursor=" + start_cursor

        response = requests.get(url, headers=self.headers, timeout=self.config.NOTION_API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503 and first_call:
            print("Retrying after 1 second...")
            time.sleep(1)
            return self.get_page_content_blocks(page_id, first_call=False, start_cursor=start_cursor, page_size=page_size)
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

    def get_page_properties(self, page_id, property_id, first_call=True, start_cursor=None, page_size=100):
        url = f"{self.base_url}pages/{page_id}/properties/{property_id}?page_size={page_size}"
        if start_cursor:
            url += "&start_cursor=" + start_cursor

        response = requests.get(url, headers=self.headers, timeout=self.config.NOTION_API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503 and first_call:
            print("Retrying after 1 second...")
            time.sleep(1)
            return self.get_page_properties(page_id, property_id, first_call=False, start_cursor=start_cursor, page_size=page_size)
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


    def get_database_metadata(self, database_id):
        url = f"{self.base_url}databases/{database_id}"
        response = requests.get(url, headers=self.headers, timeout=self.config.NOTION_API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch database info: {response.status_code} - {response.text}\nurl={url}")

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
        except:
            return self.get_page_metadata(root_id)
