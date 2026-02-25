import json
import os
from datetime import datetime

def _ts():
    return datetime.utcnow().isoformat() + "Z"

def log_jsonl(path: str, obj: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    obj = {"ts": _ts(), **obj}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")