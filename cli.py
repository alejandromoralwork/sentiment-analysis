"""
CLI runner for the News Sentiment Analysis project.
Provides a simple command-line entry that can be packaged into
a single-file executable (EXE) for non-technical users.

Usage examples:
  python cli.py --keyword Tesla --num-articles 20
  cli.exe                # runs default workflow and writes reports

The script loads environment variables from a .env file (if present)
and writes output CSV/JSON into the `data/reports/` folder.
"""

import os
import argparse
import logging
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from src.news_fetcher import fetch_news_from_api, get_article_content
from src.sentiment import preprocess_text, analyze_sentiment_ensemble
from src.reporting import save_as_csv, save_as_json
from pathlib import Path

# configure logging for CLI
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format='%(asctime)s %(levelname)s %(message)s')

REPORTS_DIR = Path(__file__).resolve().parent / "data" / "reports"


def run(keyword: str, num_articles: int, api_key: str | None = None):
    """Run the offline analysis pipeline.

    Args:
        keyword: search phrase for NewsAPI
        num_articles: number of analyzable articles to attempt
        api_key: optional NewsAPI key (otherwise read from env/.env)
    """
    load_dotenv()
    if not api_key:
        api_key = os.environ.get("NEWS_API_KEY")

    if not api_key:
        logging.error("NEWS_API_KEY not found. See README or UserGuide for instructions.")
        return 1

    logging.info("Fetching articles for '%s' (max %d)", keyword, num_articles)
    articles = fetch_news_from_api(api_key, keyword, page_size=100)
    if not articles:
        logging.warning("No articles returned from NewsAPI for keyword: %s", keyword)
        return 1

    results = []
    processed = 0
    for article in articles:
        if processed >= num_articles:
            break
        url = article.get("url")
        if not url:
            continue

        content = get_article_content(url)
        if not content:
            continue

        cleaned_text = BeautifulSoup(content, "html.parser").get_text()
        if not cleaned_text.strip():
            continue

        text_to_analyze = preprocess_text(cleaned_text)
        if not text_to_analyze:
            continue

        sentiment_scores = analyze_sentiment_ensemble(text_to_analyze, headline=article.get('title'), return_full_scores=True)

        results.append({
            'headline': article.get('title') or 'Untitled',
            'url': url,
            'consensus_sentiment': sentiment_scores['consensus'],
            'confidence': sentiment_scores['agreement'],
            'vader_sentiment': sentiment_scores['vader'],
            'textblob_sentiment': sentiment_scores['textblob'],
            'transformer_sentiment': sentiment_scores['transformer']
        })

        processed += 1

    if not results:
        logging.warning("No analyzable articles were processed.")
        return 1

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_name = f"sentiment_report_{keyword.replace(' ', '_')}.csv"
    json_name = f"sentiment_report_{keyword.replace(' ', '_')}.json"

    save_as_csv(results, csv_name)
    save_as_json(results, json_name)

    logging.info("Reports written to %s", REPORTS_DIR)
    try:
        # Try to open the reports directory for convenience on Windows
        if os.name == 'nt':
            os.startfile(REPORTS_DIR)
    except Exception:
        pass

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="News sentiment offline runner (packagable into an EXE).")
    parser.add_argument('--keyword', '-k', default='Tesla', help='Keyword to search for')
    parser.add_argument('--num-articles', '-n', type=int, default=10, help='Number of articles to analyze')
    parser.add_argument('--api-key', help='NewsAPI key (optional, overrides .env)')
    args = parser.parse_args()

    exit_code = run(args.keyword, args.num_articles, api_key=args.api_key)
    raise SystemExit(exit_code)
