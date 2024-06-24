import requests
from src.config.config_manager import Config

class NotionAPI:
    def __init__(self):
        self.config = Config()
        self.base_url = self.config.NOTION_API_BASE_URL
        self.version = self.config.NOTION_API_VERSION
        self.headers = {
            "Authorization": f"Bearer {self.config.API_KEY}",
            "Notion-Version": self.version,
            "Content-Type": "application/json"
        }

    def get_page_content(self, page_id):
        url = f"{self.base_url}pages/{page_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch page content: {response.status_code}")

    def get_block_children(self, block_id):
        url = f"{self.base_url}blocks/{block_id}/children"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch block children: {response.status_code}")
