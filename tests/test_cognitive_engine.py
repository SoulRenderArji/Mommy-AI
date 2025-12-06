import pytest
from services.cognitive_engine import CognitiveEngine


class DummyLearning:
    def __init__(self, local_response=None):
        self.local_response = local_response

    def can_handle_locally(self, query):
        return (True, self.local_response) if self.local_response is not None else (False, None)


def test_creative_preference_selects_creative_option():
    # If user profile sets high creativity_bias, engine should favor creative option
    engine = CognitiveEngine(language_understanding=None, learning_system=None)
    profile = {"cognitive_preferences": {"creativity_bias": 0.9}}

    trace = engine.decide("Give me novel ideas for storage", "hailey", profile=profile)
    assert trace.selected_option is not None
    assert trace.selected_option.get("type") == "creative", "Engine should select creative option when user prefers creativity"


def test_local_preference_selects_local_when_available():
    # If learning system can handle locally, engine should prefer local option
    dummy = DummyLearning(local_response="Stored answer from memory")
    engine = CognitiveEngine(language_understanding=None, learning_system=dummy)

    trace = engine.decide("What was my last note?", "hailey", profile=None)
    assert trace.selected_option is not None
    assert trace.selected_option.get("type") == "local", "Engine should pick local option when available"
    assert trace.perception.get("local_response") == "Stored answer from memory"


def test_summarize_trace_levels():
    engine = CognitiveEngine(language_understanding=None, learning_system=None)
    trace = engine.decide("Test summary", "hailey", profile=None)

    summary = engine.summarize_trace(trace, level="summary")
    assert "selected_option" in summary and "confidence" in summary

    detailed = engine.summarize_trace(trace, level="detailed")
    # Detailed should include perception and interpretation keys
    assert "perception" in detailed and "interpretation" in detailed


if __name__ == "__main__":
    pytest.main(["-q"])