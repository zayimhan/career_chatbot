import os
import requests
from datetime import datetime

def push(title: str, message: str):
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    if not token or not user:
        return

    payload = {
        "token": token,
        "user": user,
        "message": f"{title}\n\n{message}",
    }
    try:
        requests.post("https://api.pushover.net/1/messages.json", data=payload, timeout=10)
    except Exception:
        # notification failure should never crash the agent
        pass

def ts():
    return datetime.utcnow().isoformat() + "Z"