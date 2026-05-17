import json
from pathlib import Path

import pandas as pd
import logging


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"


def _resolve_output_path(filename):
    output_path = Path(filename)
    if output_path.is_absolute():
        return output_path

    # make sure the reports folder is there
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR / output_path.name

def save_as_csv(data, filename="report.csv"):
    # dump the rows to csv, plain and simple
    df = pd.DataFrame(data)
    output_path = _resolve_output_path(filename)
    df.to_csv(output_path, index=False, encoding="utf-8")
    # small print so we know where it went
    logging.info("Report saved to %s", output_path)

def save_as_json(data, filename="report.json"):
    # save json and keep unicode as it is
    output_path = _resolve_output_path(filename)
    with open(output_path, 'w', encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    # same little message for json
    logging.info("Report saved to %s", output_path)
