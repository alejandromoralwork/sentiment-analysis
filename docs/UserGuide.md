# User Guide (Marketing Team)

This guide explains how to run the News Sentiment Analysis tool and how to interpret the results. No programming knowledge is required.

## Overview

The product fetches recent news articles for a search term you enter and analyzes each article to produce a sentiment label: Positive, Neutral, or Negative. The tool saves a report you can open in Excel or any text editor.

## Quick start (executable)

1. Obtain the compiled executable file (`IA_Sentiment.exe`) from the project deliverables.
2. Place it in a folder and double-click `IA_Sentiment.exe` to run the web application. The program will:
   - Use the built-in (test) NewsAPI key if available.
   - Search for the default keyword ("Tesla").
   - Produce CSV and JSON reports in a `data/reports/` folder next to the executable.

3. To run with a different search term, open a command prompt in the folder and run:

```powershell
IA_Sentiment.exe --keyword "artificial intelligence" --num-articles 20
```

## What the reports contain

- `headline` — The article headline.
- `url` — Link to the original article.
- `consensus_sentiment` — Final label after combining model votes.
- `confidence` — Agreement score (0.0–1.0) indicating how many models voted the same way.
- `vader_sentiment`, `textblob_sentiment`, `transformer_sentiment` — Individual model labels.

Open the CSV in Excel for filtering and sorting (e.g., show only Negative articles).

## Interpretation guidance

- Use the consensus column to get a quick view of the overall sentiment for the search term.
- Use `confidence` to filter for stronger signals (e.g., confidence >= 0.67 means at least 2/3 models agreed).
- Review individual model columns if you want to understand why the consensus was reached.

## Troubleshooting

- If the program reports `NEWS_API_KEY not found`, ask your administrator to provide an API key and set it following the Developer Guide, or use the provided `.env` file.
- If no articles are returned, try a broader keyword or increase `--num-articles`.

## Support

If you need changes (different exported formats, scheduled runs, or a GUI wrapper), contact the development team and include the `data/reports/` files you produced.
