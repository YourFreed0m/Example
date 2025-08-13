from __future__ import annotations
import json
import os
from typing import Any, Dict

SAVE_PATH = os.path.expanduser("~/.pycraft_save.json")


def save_state(state: Dict[str, Any]) -> None:
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def load_state() -> Dict[str, Any]:
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}