import os
import yaml
from dotenv import load_dotenv
from typing import Dict, Any

class Config:
    def __init__(self):
        load_dotenv()  # Load environment variables from .env file

        # Load constants from environment variables
        self.API_KEY: str = os.getenv('API_KEY', '')
        self.DATABASE_URL: str = os.getenv('DATABASE_URL', '')
        self.CACHE_DIR: str = os.getenv('CACHE_DIR', '')

        # Load configuration from config.yaml
        with open('config/config.yaml', 'r') as config_file:
            config_data: Dict[str, Any] = yaml.safe_load(config_file)

        # Notion API configuration
        self.NOTION_API_BASE_URL: str = config_data['notion_api']['base_url']
        self.NOTION_API_VERSION: str = config_data['notion_api']['version']

        # Pocket API configuration
        self.POCKET_API_BASE_URL: str = config_data['pocket_api']['base_url']

        # LLM configuration
        self.LLM_MODEL: str = config_data['llm']['model']
        self.LLM_TEMPERATURE: float = config_data['llm']['temperature']
        self.LLM_MAX_TOKENS: int = config_data['llm']['max_tokens']

        # Neo4j configuration
        self.NEO4J_HOST: str = config_data['neo4j']['host']
        self.NEO4J_PORT: int = config_data['neo4j']['port']
        self.NEO4J_USER: str = config_data['neo4j']['user']
        self.NEO4J_PASSWORD: str = config_data['neo4j']['password']

        # Cache configuration
        self.CACHE_EXPIRATION_TIME: int = config_data['cache']['expiration_time']

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        This method is kept for backward compatibility and for accessing
        any additional configuration values that might be added in the future.
        """
        keys = key.split('.')
        value = self.__dict__
        for k in keys:
            value = value.get(k, {})
        return value if value != {} else default

# Usage example:
if __name__ == "__main__":
    config = Config()
    print(f"Notion API Base URL: {config.NOTION_API_BASE_URL}")
    print(f"LLM Model: {config.LLM_MODEL}")
    print(f"Neo4j Host: {config.NEO4J_HOST}")
    # You can still use the get_config method for flexibility
