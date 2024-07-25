from typing import Dict, Any

import yaml
from dotenv import load_dotenv
from pyaml_env import parse_config


class Config:
    def __init__(self):
        load_dotenv()  # Load environment variables from .env file

        # Load configuration from config.yaml
        config_data: Dict[str, Any] = parse_config('config/config.yaml', tag=None, default_value='')

        # Notion API configuration
        notion_config = config_data['notion_api']
        self.NOTION_API_KEY: str = notion_config['api_key']
        self.NOTION_API_BASE_URL: str = notion_config['base_url']
        self.NOTION_API_VERSION: str = notion_config['version']
        self.NOTION_API_TIMEOUT: int = notion_config['timeout']
        self.NOTION_CACHE_TTL_SECONDS: int = notion_config['cache_ttl_seconds']
        self.NOTION_CACHE_PATH: str = notion_config['cache_path']
        self.NOTION_PAGE_MAX_DEPTH: int = notion_config['page_max_depth']
        self.NOTION_ADD_ARCHIVED_PAGE_NODES: bool = notion_config['add_archived_page_nodes']
        self.NOTION_ADD_REMOVED_PAGE_NODES: bool = notion_config['add_removed_page_nodes']
        self.NOTION_CREATE_UNPROCESSED_NODES: bool = notion_config['create_unprocessed_graph_nodes']
        self.NOTION_RECURSIVE_PROCESS_REFERENCE_PAGES: bool = notion_config['recursive_process_reference_pages']
        self.NOTION_MARKDOWN_INDENT: str = notion_config['markdown_parser_options']['indent']
        self.NOTION_MARKDOWN_PARSER_EXCLUDED_PROPERTY_TYPES: list = notion_config['markdown_parser_options']['excluded_property_types']
        self.NOTION_MARKDOWN_PARSER_EXCLUDED_BLOCK_TYPES: list = notion_config['markdown_parser_options']['excluded_block_types']

        # Pocket API configuration
        self.POCKET_API_BASE_URL: str = config_data['pocket_api']['base_url']

        # LLM configuration
        llm_config = config_data['llm']
        self.OPENAI_API_KEY: str = llm_config['api_key']
        self.LLM_MODEL: str = llm_config['model']
        self.LLM_TEMPERATURE: float = llm_config['temperature']
        self.LLM_MAX_TOKENS: int = llm_config['max_tokens']

        # Neo4j configuration
        neo4j_config = config_data['neo4j']
        self.NEO4J_URI: str = neo4j_config['uri']
        self.NEO4J_USER: str = neo4j_config['user']
        self.NEO4J_PASSWORD: str = neo4j_config['password']

        # Cache configuration
        cache_config = config_data['cache']
        self.CACHE_ENABLED: int = cache_config['enabled']
        self.CACHE_PATH: str = cache_config['path']
        self.CACHE_TTL_SECONDS: int = cache_config['ttl_seconds']

        self.WEB_PARSER_TIMEOUT: int = config_data['web_parser']['timeout']

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
    print(f"Neo4j Host: {config.NEO4J_URI}")
