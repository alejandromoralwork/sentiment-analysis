import pandas as pd
from sklearn.metrics import classification_report, accuracy_score
from sentiment import (
    analyze_sentiment_vader,
    analyze_sentiment_textblob,
    analyze_sentiment_transformer
)

def evaluate_models():
    """
    load the validation data and check the models.
    """
    df = pd.read_csv('data/validation.csv')
    
    # transformer only does positive and negative, so drop neutral rows
    df_binary = df[df['sentiment'] != 'neutral']

    models = {
        "VADER": (analyze_sentiment_vader, df),
        "TextBlob": (analyze_sentiment_textblob, df),
        "Transformer": (analyze_sentiment_transformer, df_binary)
    }

    for model_name, (model_func, eval_df) in models.items():
        print(f"--- Evaluating {model_name} ---")
        
        # get model guesses
        predictions = eval_df['text'].apply(model_func)
        
        # real labels from the file
        true_labels = eval_df['sentiment']
        
        # print the numbers
        accuracy = accuracy_score(true_labels, predictions)
        report = classification_report(true_labels, predictions, zero_division=0)
        
        print(f"Accuracy: {accuracy:.4f}")
        print("Classification Report:")
        print(report)
        print("-" * 30)

if __name__ == "__main__":
    evaluate_models()
