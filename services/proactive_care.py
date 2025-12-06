"""
Proactive Care System for Mommy AI

This module tracks significant user events over a rolling time window
to calculate a 'resilience index' and proactively trigger interventions
when a user's well-being appears to be under strain.
"""

import time
import json
import os
import logging
import requests
from threading import Thread, Event

STATE_FILE = "hailey_state.json"
TIME_WINDOW_SECONDS = 24 * 60 * 60  # 24 hours
CHECK_INTERVAL_SECONDS = 15 * 60    # Every 15 minutes
RESILIENCE_THRESHOLD = 5            # Trigger intervention if score is this or lower
API_URL = "http://127.0.0.1:5000/ask"

def log_event(event_type: str, magnitude: int = 1):
    """Logs a significant event for Hailey."""
    if not os.path.exists(STATE_FILE):
        state = {"events": []}
    else:
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            state = {"events": []}

    state["events"].append({
        "timestamp": time.time(),
        "type": event_type,
        "magnitude": magnitude
    })

    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)
    logging.info(f"[Proactive Care] Logged event: {event_type} (magnitude: {magnitude})")

def _calculate_resilience() -> int:
    """Calculates Hailey's resilience index based on recent events."""
    if not os.path.exists(STATE_FILE):
        return 20  # Default to a healthy score

    with open(STATE_FILE, 'r') as f:
        state = json.load(f)

    now = time.time()
    recent_events = [e for e in state["events"] if now - e["timestamp"] < TIME_WINDOW_SECONDS]

    # Clean up old events
    state["events"] = recent_events
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

    score = 20  # Start with a baseline healthy score
    for event in recent_events:
        if event["type"] == "chore_completed":
            score += 1 * event["magnitude"]
        elif event["type"] == "pain_event":
            score += 2 * event["magnitude"] # Per instructions, pain events are weighted
        elif event["type"] == "meltdown":
            score -= 5 * event["magnitude"]

    logging.info(f"[Proactive Care] Calculated resilience index: {score}")
    return score

def _trigger_intervention(score: int):
    """Triggers an AI intervention if the resilience score is low."""
    logging.warning(f"[Proactive Care] Resilience score is {score}, below threshold of {RESILIENCE_THRESHOLD}. Triggering intervention.")
    try:
        prompt = "My proactive care system has detected that Hailey's resilience index is low. I need to check in on her. I will gently ask her how she's feeling and suggest we enter 'Protocol Green' for some rest and quiet time. I will be extra nurturing and supportive."
        payload = {"user": "rowan", "query": prompt}
        requests.post(API_URL, json=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        logging.error(f"[Proactive Care] Could not trigger intervention: {e}")

def run_care_monitor(stop_event: Event):
    """The main loop for the proactive care monitor thread."""
    logging.info("[Proactive Care] Monitor started. Checking resilience every 15 minutes.")
    while not stop_event.is_set():
        try:
            resilience_score = _calculate_resilience()
            if resilience_score <= RESILIENCE_THRESHOLD:
                _trigger_intervention(resilience_score)
        except Exception as e:
            logging.error(f"[Proactive Care] Error in monitoring loop: {e}")
        
        # Wait for the next interval, but check for the stop event periodically
        stop_event.wait(timeout=CHECK_INTERVAL_SECONDS)
    logging.info("[Proactive Care] Monitor shutting down.")

if __name__ == '__main__':
    # Example of logging events
    logging.basicConfig(level=logging.INFO)
    log_event("chore_completed", 1)
    time.sleep(1)
    log_event("pain_event", 1)
    time.sleep(1)
    log_event("meltdown", 1)
    _calculate_resilience()