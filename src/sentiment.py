import re
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from transformers import pipeline
import transformers as _transformers_pkg
import logging

# VADER is the quick one we use
vader_analyzer = SentimentIntensityAnalyzer()

# transformer model for sentiment, not NLI
_TRANSFORMER_MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
_transformer_pipeline = None

def _get_transformer_pipeline():
    """Lazily instantiate and cache the HuggingFace sentiment pipeline.

    This avoids downloading model weights at module import time and allows
    the application to log model and library versions for reproducibility.
    """
    global _transformer_pipeline
    if _transformer_pipeline is None:
        try:
            _transformer_pipeline = pipeline("sentiment-analysis", model=_TRANSFORMER_MODEL_NAME)
            logging.info("Loaded transformer pipeline: %s (transformers %s)", _TRANSFORMER_MODEL_NAME, _transformers_pkg.__version__)
        except Exception:
            logging.exception("Failed to load transformer pipeline %s", _TRANSFORMER_MODEL_NAME)
            _transformer_pipeline = None
    return _transformer_pipeline


def _chunk_text_for_transformer(text, max_tokens=384, overlap=48):
    """
    split long text into smaller chunks so the transformer does not hit the
    512 token limit.
    """
    if not text or not text.strip():
        return []

    pipeline_inst = _get_transformer_pipeline()
    if pipeline_inst is None:
        return []
    tokenizer = pipeline_inst.tokenizer
    token_ids = tokenizer.encode(text, add_special_tokens=False)
    if len(token_ids) <= max_tokens:
        return [text]

    chunks = []
    step = max_tokens - overlap
    for start in range(0, len(token_ids), step):
        chunk_ids = token_ids[start:start + max_tokens]
        if not chunk_ids:
            break
        chunk_text = tokenizer.decode(chunk_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)
        if chunk_text.strip():
            chunks.append(chunk_text.strip())

    return chunks


def _get_transformer_scores(text):
    """
    get a label -> score map from the transformer pipeline.
    """
    pipeline_inst = _get_transformer_pipeline()
    if pipeline_inst is None:
        return {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}

    raw_result = pipeline_inst(
        text,
        truncation=True,
        max_length=512,
        clean_up_tokenization_spaces=False,
        return_all_scores=True
    )

    if raw_result and isinstance(raw_result[0], list):
        raw_result = raw_result[0]

    scores = {}
    for item in raw_result:
        label = _normalize_transformer_label(item.get('label', 'neutral'))
        score = float(item.get('score', 0.0))
        scores[label] = score

    if 'positive' not in scores:
        scores['positive'] = 0.0
    if 'negative' not in scores:
        scores['negative'] = 0.0
    if 'neutral' not in scores:
        scores['neutral'] = 0.0

    return scores


def _normalize_transformer_label(label):
    label = str(label).lower()
    if "positive" in label or label == "label_2":
        return "positive"
    if "negative" in label or label == "label_0":
        return "negative"
    if "neutral" in label or label == "label_1":
        return "neutral"
    return "neutral"


def preprocess_text(text):
    """
    clean text before sentiment work.
    strips urls, emails, extra space, and html bits.
    """
    if not text:
        return ""
    
    # drop urls
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    # drop emails too
    text = re.sub(r'\S+@\S+', '', text)
    # fix a few html entities
    text = text.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    # squash extra spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def analyze_sentiment_vader(text, compound_threshold=0.1):
    """
    VADER sentiment, gives positive, negative, or neutral.
    Threshold is a bit stricter so it does not call things positive too easy.
    """
    if not text or not text.strip():
        return 'neutral'
    
    score = vader_analyzer.polarity_scores(text)
    if score['compound'] >= compound_threshold:
        return 'positive'
    elif score['compound'] <= -compound_threshold:
        return 'negative'
    else:
        return 'neutral'


def analyze_sentiment_textblob(text, headline=None):
    """
    TextBlob sentiment, same three labels.
    Simple one, but okay for a quick compare.
    """
    if not text or not text.strip():
        return 'neutral'
    
    text_for_blob = text
    if headline and headline.strip():
        text_for_blob = f"{headline.strip()}. {text}"

    analysis = TextBlob(text_for_blob)
    # a smaller buffer so negative news has a better chance to show up
    if analysis.sentiment.polarity > 0.08:
        return 'positive'
    elif analysis.sentiment.polarity < -0.06:
        return 'negative'
    else:
        return 'neutral'


def analyze_sentiment_transformer(text):
    """
    transformer sentiment with the model we picked.
    returns a simple label in lower case.
    """
    if not text or not text.strip():
        return 'neutral'
    
    try:
        chunks = _chunk_text_for_transformer(text)
        if not chunks:
            return 'neutral'

        best_label = 'neutral'
        best_margin = float('-inf')
        best_score = float('-inf')

        for chunk in chunks[:4]:
            # keep the article lead and the strongest chunk instead of averaging
            scores = _get_transformer_scores(chunk)
            chunk_label = max(scores, key=scores.get)
            chunk_score = scores[chunk_label]
            margin = chunk_score - scores.get('neutral', 0.0)

            if chunk_label in ('positive', 'negative') and (margin > best_margin or (margin == best_margin and chunk_score > best_score)):
                best_label = chunk_label
                best_margin = margin
                best_score = chunk_score
            elif best_label == 'neutral' and chunk_label == 'neutral' and chunk_score > best_score:
                best_score = chunk_score

        return best_label
    except Exception:
        logging.exception("Transformer analysis failed")
        return 'neutral'


def analyze_sentiment_ensemble(text, headline=None, return_full_scores=False):
    """
    run all three models and take the one with most votes.
    if asked, also give back the model-by-model result.
    """
    if not text or not text.strip():
        if return_full_scores:
            return {
                'consensus': 'neutral',
                'agreement': 1.0,
                'vader': 'neutral',
                'textblob': 'neutral',
                'transformer': 'neutral'
            }
        return 'neutral'
    
    # clean text first so the models dont get garbage
    cleaned = preprocess_text(text)
    
    # ask all three models
    vader = analyze_sentiment_vader(cleaned)
    textblob = analyze_sentiment_textblob(cleaned, headline=headline)
    transformer = analyze_sentiment_transformer(cleaned)
    
    votes = [vader, textblob, transformer]
    
    # pick the label with most votes
    vote_counts = Counter(votes)
    consensus = vote_counts.most_common(1)[0][0]  # most voted one
    agreement = round(vote_counts[consensus] / 3, 2)  # rough confidence score
    
    if return_full_scores:
        return {
            'consensus': consensus,
            'agreement': agreement,
            'vader': vader,
            'textblob': textblob,
            'transformer': transformer
        }
    
    return consensus
