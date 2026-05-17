import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
import json
import webbrowser
import threading
import socket
from contextlib import asynccontextmanager
import uvicorn
import logging
import sys

# keep imports tied to the project root
from src.news_fetcher import fetch_news_from_api, get_article_content
from bs4 import BeautifulSoup
from src.sentiment import (
    analyze_sentiment_vader,
    analyze_sentiment_textblob,
    analyze_sentiment_transformer,
    preprocess_text,
    analyze_sentiment_ensemble
)
from src.reporting import save_as_csv, save_as_json

# load env vars from .env if it is there
load_dotenv()

# basic logging for the app
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format='%(asctime)s %(levelname)s %(message)s')

PROJECT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
REPORT_JSON = REPORTS_DIR / "sentiment_report.json"
LEGACY_REPORT_JSON = PROJECT_ROOT / "sentiment_report.json"
NEWSAPI_PAGE_SIZE = 100
NEWSAPI_MAX_PAGES = 20
MAX_REQUESTED_ARTICLES = 500


def load_latest_report():
    # check the new reports folder first, then the old root file if needed
    for report_path in (REPORT_JSON, LEGACY_REPORT_JSON):
        if report_path.exists():
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # should be a list, if not then just skip it
                if isinstance(data, list):
                    return data
            except Exception as e:
                # file may be bad or half written, just move on
                logging.warning("Could not load report from %s: %s", report_path, e)

    # nothing usable found, so return empty list for the page
    return []


def open_browser():
    """
    open browser after a short wait.
    """
    try:
        port = SERVER_PORT or int(os.environ.get("PORT", os.environ.get("APP_PORT", 8000)))
        webbrowser.open_new_tab(f"http://127.0.0.1:{port}")
    except Exception as e:
        logging.warning("Could not open browser: %s", e)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup stuff
    logging.info("Starting up...")
    # tiny delay so the server has time to wake up
    threading.Timer(2.5, open_browser).start()
    yield
    # shutdown stuff
    logging.info("Shutting down...")

app = FastAPI(lifespan=lifespan)
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# static files live in templates too
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "initial_results": load_latest_report(),
        },
    )


@app.get("/api/reports/latest")
async def get_latest_report():
    return JSONResponse({"results": load_latest_report()})

async def analysis_pipeline(websocket: WebSocket, keyword: str, num_articles: int):
    """
    send progress updates while the news gets analysed.
    """
    await websocket.send_text(f"INFO: Starting analysis for keyword: '{keyword}'...")
    
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        await websocket.send_text("ERROR: NEWS_API_KEY not found. Please set it in your .env file.")
        return

    target_count = max(1, min(int(num_articles), MAX_REQUESTED_ARTICLES))
    await websocket.send_text(f"INFO: Targeting {target_count} analyzed articles for keyword '{keyword}'.")

    results = []
    seen_urls = set()
    fetched_candidates = 0

    for page in range(1, NEWSAPI_MAX_PAGES + 1):
        if len(results) >= target_count:
            break

        remaining = target_count - len(results)
        await websocket.send_text(f"INFO: Fetching NewsAPI page {page} ({remaining} remaining)...")

        try:
            articles = fetch_news_from_api(api_key, keyword, page_size=NEWSAPI_PAGE_SIZE, page=page)
        except Exception as e:
            await websocket.send_text(f"ERROR: Failed to fetch NewsAPI page {page}: {e}")
            break

        if not articles:
            await websocket.send_text("INFO: NewsAPI returned no more articles.")
            break

        for article in articles:
            if len(results) >= target_count:
                break

            article_url = article.get('url')
            if not article_url or article_url in seen_urls:
                continue

            seen_urls.add(article_url)
            fetched_candidates += 1
            headline = article.get('title') or "Untitled"
            await websocket.send_text(f"INFO: Processing candidate {fetched_candidates}: {headline[:50]}...")

            content = get_article_content(article_url)
            if not content:
                await websocket.send_text(f"WARNING: Could not retrieve content for candidate {fetched_candidates}. Skipping.")
                continue
            cleaned_text = BeautifulSoup(content, "html.parser").get_text()
            if not cleaned_text.strip():
                await websocket.send_text(f"WARNING: Candidate {fetched_candidates} has no text after cleaning. Skipping.")
                continue

            # use full article text here, not just headline stuff
            text_to_analyze = preprocess_text(cleaned_text)
            
            if not text_to_analyze:
                await websocket.send_text(f"WARNING: Candidate {fetched_candidates} has no valid text. Skipping.")
                continue

            # let the three models vote on it
            sentiment_scores = analyze_sentiment_ensemble(text_to_analyze, headline=headline, return_full_scores=True)

            results.append({
                'headline': headline,
                'url': article_url,
                'consensus_sentiment': sentiment_scores['consensus'],
                'confidence': sentiment_scores['agreement'],
                'vader_sentiment': sentiment_scores['vader'],
                'textblob_sentiment': sentiment_scores['textblob'],
                'transformer_sentiment': sentiment_scores['transformer']
            })
            await asyncio.sleep(0.05)

    if len(results) < target_count:
        await websocket.send_text(
            f"WARNING: Requested {target_count} articles but only {len(results)} analyzable articles were found."
        )

    if results:
        save_as_csv(results, "sentiment_report.csv")
        save_as_json(results, "sentiment_report.json")
        await websocket.send_text("INFO: Analysis complete. Sending results.")
        # send the final result back as json
        await websocket.send_text(json.dumps({"type": "results", "data": results}))
    else:
        await websocket.send_text("WARNING: No articles were processed successfully.")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # wait for the next request from the page
            data = await websocket.receive_text()
            params = json.loads(data)
            keyword = params.get("keyword", "Tesla")
            num_articles = params.get("num_articles", 10)
            try:
                num_articles = int(num_articles)
            except (TypeError, ValueError):
                num_articles = 10
            
            # run the analysis
            await analysis_pipeline(websocket, keyword, num_articles)
            await websocket.send_text("INFO: Ready for new analysis.")

    except WebSocketDisconnect:
        logging.info("Client disconnected")
    except Exception as e:
        logging.exception("An error occurred in websocket handler: %s", e)
        try:
            await websocket.send_text(f"ERROR: An unexpected error occurred on the server: {e}")
        except:
            pass

if __name__ == "__main__":
    # If a server is already running on any preferred port, open its UI and exit.
    def find_running_server(start: int = 8000, host: str = "127.0.0.1", max_look: int = 50) -> int | None:
        for p in range(start, start + max_look):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.settimeout(0.25)
                    s.connect((host, p))
                    return p
                except Exception:
                    continue
        return None

    # determine a usable port: prefer env `PORT` / `APP_PORT`, otherwise 8000
    def find_free_port(preferred: int = 8000, host: str = "127.0.0.1", max_tries: int = 50) -> int:
        port = preferred
        for _ in range(max_tries):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind((host, port))
                    return port
                except OSError:
                    port += 1
        raise RuntimeError(f"No free port found starting at {preferred}")

    preferred = int(os.environ.get("PORT", os.environ.get("APP_PORT", 8000)))

    # If a server is already running on a nearby port, open it and exit (useful for double-click UX)
    running = find_running_server(preferred)
    if running:
        logging.info("Detected existing server on port %s — opening browser and exiting", running)
        try:
            webbrowser.open_new_tab(f"http://127.0.0.1:{running}")
        except Exception:
            pass
        sys.exit(0)

    try:
        SERVER_PORT = find_free_port(preferred)
    except Exception as e:
        logging.exception("Could not find a free port: %s", e)
        raise

    if SERVER_PORT != preferred:
        logging.info("Preferred port %s busy — using %s instead", preferred, SERVER_PORT)

    uvicorn.run(app, host="127.0.0.1", port=SERVER_PORT)
