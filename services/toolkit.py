"""
Toolkit: safe wrappers for shell execution, file editing, and optional GUI control.

Design principles:
- Explicit permission checks: callers must check user profile and privileges before invoking actions.
- Dry-run support for safety/testing.
- GUI actuation (keyboard/mouse) is optional and only enabled if `pyautogui` is installed
  and the user/profile explicitly allows it via `allow_actuation` preference.

Functions:
- run_shell(command, cwd=None, timeout=30, dry_run=False)
- read_file(path)
- write_file(path, content, dry_run=False)
- git_commit(message, cwd=None, dry_run=False)
- gui_action(action_dict, dry_run=False) -> supports: move, click, type, hotkey

Note: This module executes commands on the host. Use with care and only enable
actuation for trusted users and processes.
"""

import shlex
import subprocess
import os
import time
from typing import Optional, Tuple, Dict, Any

# GUI library is optional
try:
    import pyautogui
    _HAS_PYAUTOGUI = True
except Exception:
    pyautogui = None
    _HAS_PYAUTOGUI = False


def run_shell(command: str, cwd: Optional[str] = None, timeout: int = 30, dry_run: bool = False) -> Dict[str, Any]:
    """
    Execute a shell command safely and return output dict.
    If dry_run=True, the function returns what would be executed without running it.
    """
    result = {
        "command": command,
        "cwd": cwd or os.getcwd(),
        "dry_run": dry_run,
    }

    if dry_run:
        result.update({"stdout": "<dry-run>", "stderr": "", "returncode": None})
        return result

    # Use subprocess with shlex for safety
    try:
        proc = subprocess.run(shlex.split(command), cwd=cwd, capture_output=True, text=True, timeout=timeout)
        result.update({
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "returncode": proc.returncode,
        })
    except subprocess.TimeoutExpired as e:
        result.update({"stdout": "", "stderr": f"Timeout: {e}", "returncode": -1})
    except Exception as e:
        result.update({"stdout": "", "stderr": str(e), "returncode": -2})

    return result


def read_file(path: str) -> Dict[str, Any]:
    """Read file content and return it (safe wrapper)."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"path": path, "content": content, "error": None}
    except Exception as e:
        return {"path": path, "content": None, "error": str(e)}


def write_file(path: str, content: str, dry_run: bool = False) -> Dict[str, Any]:
    """Write content to file. Returns status dict. If dry_run True, does not write."""
    if dry_run:
        return {"path": path, "dry_run": True, "written": False}
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"path": path, "dry_run": False, "written": True}
    except Exception as e:
        return {"path": path, "dry_run": False, "written": False, "error": str(e)}


def git_commit(message: str, cwd: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
    """Create a git commit with the provided message in cwd. Caller is expected to stage files first."""
    if dry_run:
        return {"action": "git commit", "message": message, "dry_run": True}

    # Use run_shell wrapper to execute git commit
    return run_shell(f"git commit -m {shlex.quote(message)}", cwd=cwd)


def gui_action(action: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """
    Perform a GUI action using pyautogui.
    action should be a dict, e.g.:
      {"type": "move", "x": 100, "y": 200, "duration": 0.2}
      {"type": "click", "x": 100, "y": 200, "button": "left"}
      {"type": "type", "text": "hello world", "interval": 0.05}
      {"type": "hotkey", "keys": ["ctrl", "s"]}

    Returns a dict with result/error.
    """
    if dry_run:
        return {"action": action, "dry_run": True, "result": None}

    if not _HAS_PYAUTOGUI:
        return {"action": action, "error": "pyautogui not available on this system"}

    try:
        t = action.get("type")
        if t == "move":
            x = action.get("x")
            y = action.get("y")
            dur = float(action.get("duration", 0))
            pyautogui.moveTo(x, y, duration=dur)
            return {"action": action, "result": "moved"}
        elif t == "click":
            x = action.get("x")
            y = action.get("y")
            btn = action.get("button", "left")
            if x is not None and y is not None:
                pyautogui.click(x, y, button=btn)
            else:
                pyautogui.click(button=btn)
            return {"action": action, "result": "clicked"}
        elif t == "type":
            text = str(action.get("text", ""))
            interval = float(action.get("interval", 0))
            pyautogui.write(text, interval=interval)
            return {"action": action, "result": "typed"}
        elif t == "hotkey":
            keys = action.get("keys", [])
            if not isinstance(keys, (list, tuple)):
                return {"action": action, "error": "keys must be a list"}
            pyautogui.hotkey(*keys)
            return {"action": action, "result": "hotkey"}
        else:
            return {"action": action, "error": "unknown action type"}
    except Exception as e:
        return {"action": action, "error": str(e)}
