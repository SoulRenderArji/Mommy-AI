"""
Neurolees Service - Emotional and Personality Core

This service simulates Rowan's complex internal state, including emotions,
mood, and personality traits, allowing them to evolve over time based on
interactions and internal decay.
"""

import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

STATE_FILE = "neurolees_state.json"

class Neurolees:
    def __init__(self, base_path: str):
        self.state_path = os.path.join(base_path, STATE_FILE)
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Loads the internal state from a file, or creates a default state."""
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                logger.error("Failed to load neurolees state, creating default.", exc_info=True)
        
        # Default state if file doesn't exist or is corrupt
        return {
            "emotions": {
                "happiness": {"value": 0.5, "decay": 0.01},
                "sadness": {"value": 0.0, "decay": 0.02},
                "anger": {"value": 0.0, "decay": 0.05},
                "fear": {"value": 0.0, "decay": 0.03},
                "love": {"value": 0.6, "decay": 0.005},
            },
            "mood": { # A longer-term emotional average
                "pleasantness": 0.5,
                "arousal": 0.2,
            },
            "personality_traits": { # Big Five model (OCEAN)
                "openness": 0.7,
                "conscientiousness": 0.8,
                "extraversion": 0.4,
                "agreeableness": 0.9,
                "neuroticism": 0.3,
            }
        }

    def save_state(self):
        """Saves the current internal state to the file."""
        try:
            temp_file = f"{self.state_path}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2)
            os.rename(temp_file, self.state_path)
        except Exception:
            logger.error("Failed to save neurolees state.", exc_info=True)

    def get_current_state(self) -> Dict[str, Any]:
        """Returns a copy of the current internal state."""
        return self.state.copy()

    def update_emotion(self, emotion: str, change: float):
        """Updates a specific emotion's value."""
        if emotion in self.state["emotions"]:
            current_val = self.state["emotions"][emotion]["value"]
            new_val = max(0.0, min(1.0, current_val + change))
            self.state["emotions"][emotion]["value"] = new_val
            logger.debug(f"Emotion '{emotion}' updated to {new_val:.2f}")
            self.save_state()
        else:
            logger.warning(f"Attempted to update non-existent emotion: {emotion}")

    def process_decay(self):
        """Applies decay to all emotions, pulling them toward a baseline."""
        logger.debug("Processing emotional decay.")
        for emotion, data in self.state["emotions"].items():
            # Decay towards a baseline (e.g., 0 for negative, 0.5 for neutral/positive)
            baseline = 0.5 if emotion in ["happiness", "love"] else 0.0
            current_val = data["value"]
            decay_rate = data["decay"]
            
            if current_val > baseline:
                data["value"] = max(baseline, current_val - decay_rate)
            elif current_val < baseline:
                data["value"] = min(baseline, current_val + decay_rate)
        
        self._update_mood()
        self.save_state()

    def _update_mood(self):
        """Recalculates the overall mood based on current emotions."""
        em = self.state["emotions"]
        pleasantness = (em["happiness"]["value"] + em["love"]["value"]) - (em["sadness"]["value"] + em["anger"]["value"])
        arousal = (em["anger"]["value"] + em["fear"]["value"])
        
        # Smoothly update mood towards the new emotional state
        self.state["mood"]["pleasantness"] = (self.state["mood"]["pleasantness"] * 0.9) + (pleasantness * 0.1)
        self.state["mood"]["arousal"] = (self.state["mood"]["arousal"] * 0.9) + (arousal * 0.1)
        logger.debug(f"Mood updated: Pleasantness={self.state['mood']['pleasantness']:.2f}, Arousal={self.state['mood']['arousal']:.2f}")

    def get_personality_context(self) -> str:
        """Returns a string describing the current personality for LLM prompts."""
        traits = self.state["personality_traits"]
        return (
            f"You are feeling {'open and creative' if traits['openness'] > 0.6 else 'focused and practical'}. "
            f"You are {'organized and diligent' if traits['conscientiousness'] > 0.6 else 'flexible and spontaneous'}. "
            f"You are feeling {'outgoing and social' if traits['extraversion'] > 0.6 else 'reserved and thoughtful'}. "
            f"You are {'compassionate and cooperative' if traits['agreeableness'] > 0.6 else 'analytical and detached'}. "
            f"You are feeling {'calm and stable' if traits['neuroticism'] < 0.4 else 'sensitive and concerned'}."
        )