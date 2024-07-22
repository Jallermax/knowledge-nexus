import requests
from bs4 import BeautifulSoup

from graph_rag.config.config_manager import Config

config = Config()


def get_info_from_url(url):
    response = requests.get(url, timeout=config.WEB_PARSER_TIMEOUT)
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.title.string
    description_tag = soup.find('meta', attrs={'name': 'description'})
    description = description_tag['content'] if description_tag else None
    return title, description
