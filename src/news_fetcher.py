from newsapi import NewsApiClient
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def fetch_news_from_api(api_key, keyword, page_size=20, page=1):
    """
    fetch news articles from NewsAPI.
    just a small wrapper.
    """
    newsapi = NewsApiClient(api_key=api_key)
    try:
        articles = newsapi.get_everything(
            q=keyword,
            language='en',
            sort_by='relevancy',
            page_size=page_size,
            page=page,
        )
        # ensure the response has the expected key
        return articles.get('articles', [])
    except Exception as e:
        logger.exception("Failed to fetch from NewsAPI: %s", e)
        return []


def get_article_content(url):
    """
    fetch the main text from an article page.
    not perfect, but it works most of the time.
    """
    # build a session with retries for transient errors
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=(500, 502, 503, 504))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        response = session.get(url, timeout=10)
        if response.status_code != 200:
            logger.debug("Non-200 response for %s: %s", url, response.status_code)
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        # grab paragraph text and glue it together
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text() for p in paragraphs])
        return content
    except requests.RequestException as e:
        # network problem or timeout, caller can skip this one
        logger.debug("Request failed for %s: %s", url, e)
        return None
