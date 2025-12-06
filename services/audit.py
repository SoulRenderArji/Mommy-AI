"""
Simple audit logging for tool actions.
Appends newline-delimited JSON entries to `logs/tool_audit.log`.
"""
import json
import os
from datetime import datetime
from typing import Any, Dict

LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
LOG_PATH = os.path.join(LOG_DIR, 'tool_audit.log')

os.makedirs(LOG_DIR, exist_ok=True)


def record(action: str, user: str, endpoint: str, payload: Dict[str, Any], result: Dict[str, Any], authorized: bool):
    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'action': action,
        'user': user,
        'endpoint': endpoint,
        'payload': payload,
        'result_summary': {
            'returncode': result.get('returncode') if isinstance(result, dict) else None,
            'error': result.get('error') if isinstance(result, dict) else None,
        },
        'authorized': bool(authorized),
    }
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        # Fail silently to avoid breaking tool endpoints
        pass


def read_recent(limit: int = 200):
    """Return the last `limit` audit entries as dicts."""
    try:
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-limit:]
        return [json.loads(l) for l in lines]
    except Exception:
        return []
