import os
import logging
from dotenv import load_dotenv
from news_fetcher import fetch_news_from_api, get_article_content
from bs4 import BeautifulSoup
from sentiment import (
    analyze_sentiment_vader,
    analyze_sentiment_textblob,
    analyze_sentiment_transformer,
    preprocess_text,
    analyze_sentiment_ensemble
)
from reporting import save_as_csv, save_as_json

# configure logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format='%(asctime)s %(levelname)s %(message)s')

def main():
    """
    small local runner for the news pipeline.
    """
    load_dotenv()
    # use env var for the api key, not hardcoded
    api_key = os.environ.get("NEWS_API_KEY") 
    if not api_key:
        logging.error("NEWS_API_KEY not found in .env file or as an environment variable.")
        logging.error("Get a free API key from https://newsapi.org/ and set it.")
        return

    keyword = "Tesla"
    logging.info("Fetching news for '%s'...", keyword)
    
    articles = fetch_news_from_api(api_key, keyword, page_size=100)
    
    results = []
    
    logging.info("Analyzing %d articles...", len(articles))
    for article in articles:
        content = get_article_content(article['url'])
        if not content:
            continue
            
        # strip html out and clean the text a bit
        cleaned_text = BeautifulSoup(content, "html.parser").get_text()
        
        if not cleaned_text.strip():
            continue

        # full text is better than headline only
        text_to_analyze = preprocess_text(cleaned_text)
        
        if not text_to_analyze:
            continue

        # let all three models vote
        sentiment_scores = analyze_sentiment_ensemble(text_to_analyze, headline=article['title'], return_full_scores=True)

        results.append({
            'headline': article['title'],
            'url': article['url'],
            'consensus_sentiment': sentiment_scores['consensus'],
            'confidence': sentiment_scores['agreement'],
            'vader_sentiment': sentiment_scores['vader'],
            'textblob_sentiment': sentiment_scores['textblob'],
            'transformer_sentiment': sentiment_scores['transformer']
        })

    if results:
        save_as_csv(results, "sentiment_report.csv")
        save_as_json(results, "sentiment_report.json")
    else:
        logging.warning("No articles were processed.")

if __name__ == "__main__":
    main()
