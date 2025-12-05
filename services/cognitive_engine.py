"""
Cognitive Engine for Mommy AI

Simulates high-level thought processes: perception, interpretation, option generation,
evaluation, decision, and learning update. Produces a concise, explainable trace
that can be returned to the caller when requested.

Design goals:
- Dynamic and adaptive: adjust thresholds and creative/search modes
- Accepts some things as immutable facts and marks them as "accepted"
- When appropriate, generates creative/out-of-the-box option(s)
- Produces a short, structured explanation (not raw chain-of-thought)
"""
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Tuple, Optional
import time


@dataclass
class DecisionTrace:
    timestamp: float
    perception: Dict[str, Any]
    interpretation: Dict[str, Any]
    options: List[Dict[str, Any]]
    selected_option: Dict[str, Any]
    confidence: float
    notes: List[str]


class CognitiveEngine:
    def __init__(self, language_understanding=None, learning_system=None, config: Optional[Dict] = None):
        """
        language_understanding: instance of LanguageUnderstanding (optional)
        learning_system: instance of LearningSystem (optional)
        config: tuning parameters
        """
        self.lu = language_understanding
        self.learning = learning_system
        self.config = config or {}

        # Tunable parameters with sensible defaults
        self.threshold_local_confidence = self.config.get("threshold_local_confidence", 0.7)
        self.threshold_accept_as_fact = self.config.get("threshold_accept_as_fact", 0.85)
        self.creativity_bias = self.config.get("creativity_bias", 0.2)  # 0..1, higher means more creative options
        # Prompt templates used by Mommy AI for different strategies. Templates accept named fields:
        # {system_prompt}, {personal_context}, {compact_context}, {user}, {query}, {response_style}
        self.prompt_templates = {
            "hybrid": (
                "{system_prompt}\n{personal_context}\n\n--- CONTEXT ---\n{compact_context}\n\n--- QUERY ---\n{user}: {query}\n\n"
                "Adopt a {response_style} tone and respond concisely (one short paragraph)."
            ),
            "creative": (
                "{system_prompt}\n{personal_context}\n\n--- CONTEXT ---\n{compact_context}\n\n--- QUERY ---\n{user}: {query}\n\n"
                "You are encouraged to think creatively and propose unconventional, useful workarounds or ideas. "
                "If suggesting something uncertain, mark it as a suggestion and recommend verification. "
                "Adopt a {response_style} tone."
            ),
            "llm": (
                "{system_prompt}\n{personal_context}\n\n--- CONTEXT ---\n{compact_context}\n\n--- QUERY ---\n{user}: {query}\n\n"
                "Adopt a {response_style} tone. If you need to ask for clarification, do so briefly, then answer."
            ),
        }

    def _perceive(self, query: str, user: str, profile: Optional[Dict]) -> Dict[str, Any]:
        # Run language understanding if available
        lu_summary = self.lu.get_query_summary(query) if self.lu else {}
        # Check learned knowledge availability
        can_handle_locally, local_response = (False, None)
        if self.learning:
            can_handle_locally, local_response = self.learning.can_handle_locally(query)
        perception = {
            "query": query,
            "user": user,
            "profile": profile,
            "lu_summary": lu_summary,
            "can_handle_locally": can_handle_locally,
            "local_response_exists": bool(local_response),
            "local_response": local_response,
        }
        return perception

    def _interpret(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        # Turn perception into higher-level interpretation
        intent = perception.get("lu_summary", {}).get("intent", {}).get("name") if perception.get("lu_summary") else None
        sentiment = perception.get("lu_summary", {}).get("sentiment", {}).get("sentiment") if perception.get("lu_summary") else None
        entities = perception.get("lu_summary", {}).get("entities") if perception.get("lu_summary") else {}

        interpretation = {
            "intent": intent or "unknown",
            "sentiment": sentiment or "neutral",
            "entities": entities or {},
            "local_available": perception.get("can_handle_locally")
        }
        return interpretation

    def _generate_options(self, perception: Dict[str, Any], interpretation: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Produce candidate strategies for answering the query. Each option has a type and score.
        options = []

        # Use configured creativity bias for option scoring (may be overridden by profile)
        creativity_bias = self.creativity_bias

        # Option: Use local learned knowledge (if available)
        if perception.get("can_handle_locally"):
            options.append({
                "type": "local",
                "description": "Answer from learned/internal knowledge",
                "score": 0.9
            })

        # Option: Use compact local knowledge search + LLM summarization
        options.append({
            "type": "hybrid",
            "description": "Search local knowledge and ask LLM to summarize with context",
            "score": 0.7 + (creativity_bias * 0.05)
        })

        # Option: Use external LLM directly
        options.append({
            "type": "llm",
            "description": "Answer using external LLM (Gemini/Ollama)",
            "score": 0.6 + (creativity_bias * 0.05)
        })

        # If the intent is emotional or requires empathy, boost options that favor empathy and short responses
        if interpretation.get("intent") in ("emotional", "request_help"):
            for opt in options:
                if opt["type"] in ("local", "hybrid"):
                    opt["score"] += 0.05
                if opt["type"] == "llm":
                    opt["score"] += 0.05

        # Creativity: sometimes add an "outside the box" option with lower baseline score
        if creativity_bias > 0.0:
            creative_score = 0.4 + (creativity_bias * 0.4)  # in [0.4,0.8]
            options.append({
                "type": "creative",
                "description": "Generate creative or non-standard suggestions and workarounds",
                "score": creative_score
            })

        # Normalize and return
        # In real system, we might factor in user preferences, risk, safety, etc.
        return sorted(options, key=lambda o: o["score"], reverse=True)

    def _evaluate_and_select(self, options: List[Dict[str, Any]], interpretation: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        # Basic selection: choose highest score unless business rules override
        selected = options[0]
        confidence = selected["score"]

        # If local option exists and score exceeds threshold, prefer it and treat as "accepted" if high confidence
        if selected["type"] == "local" and confidence >= self.threshold_local_confidence:
            notes = ["Selected local knowledge because confidence exceeded local threshold."]
        else:
            notes = [f"Selected {selected['type']} option based on score."]

        # If selected is creative but confidence is low, add note to encourage follow-up checks
        if selected["type"] == "creative" and confidence < 0.5:
            notes.append("Creative option selected; recommend verification before treating as fact.")

        return selected, confidence, notes

    def build_prompt(self,
                     option_type: str,
                     query: str,
                     user: str,
                     personal_context: str,
                     compact_context: str,
                     response_style: str,
                     system_prompt: Optional[str] = None,
                     profile: Optional[Dict] = None,
                     creativity_mode: bool = False) -> Tuple[str, Optional[str]]:
        """
        Build a prompt string and optional system message based on the chosen option_type and templates.
        Returns: (prompt_text, system_message)
        """
        # Choose template
        tpl = self.prompt_templates.get(option_type, self.prompt_templates.get("llm"))

        # If creative mode requested, prefer creative template
        if creativity_mode:
            tpl = self.prompt_templates.get("creative", tpl)

        system_msg = system_prompt

        prompt_text = tpl.format(
            system_prompt=(system_prompt or ""),
            personal_context=(personal_context or ""),
            compact_context=(compact_context or ""),
            user=user,
            query=query,
            response_style=response_style,
        )

        # If profile suggests extra constraints (e.g., conservative_user), we can append guidance
        if profile and profile.get("cognitive_preferences", {}).get("conservative", False):
            prompt_text += "\n\nNote: Be conservative in assertions; clearly label uncertain suggestions."

        return prompt_text, system_msg

    def decide(self, query: str, user: str, profile: Optional[Dict] = None) -> DecisionTrace:
        """
        Main entry point. Returns a DecisionTrace dataclass containing a summarized trace
        of perception, interpretation, candidate options, the selected option, confidence, and notes.
        """
        start = time.time()
        # Apply per-user overrides from profile if present (do not mutate engine defaults)
        user_prefs = profile.get("cognitive_preferences", {}) if profile else {}
        local_threshold = user_prefs.get("threshold_local_confidence", self.threshold_local_confidence)
        accept_threshold = user_prefs.get("threshold_accept_as_fact", self.threshold_accept_as_fact)
        creativity_bias = user_prefs.get("creativity_bias", self.creativity_bias)

        perception = self._perceive(query, user, profile)
        interpretation = self._interpret(perception)
        # Generate options using possible per-user creativity bias
        # Temporarily use the per-user creativity bias by passing it via attribute
        original_creativity = self.creativity_bias
        try:
            self.creativity_bias = creativity_bias
            options = self._generate_options(perception, interpretation)
        finally:
            self.creativity_bias = original_creativity
        selected, confidence, notes = self._evaluate_and_select(options, interpretation)

        trace = DecisionTrace(
            timestamp=start,
            perception=perception,
            interpretation=interpretation,
            options=options,
            selected_option=selected,
            confidence=confidence,
            notes=notes
        )

        return trace

    def is_fact_accepted(self, statement_confidence: float) -> bool:
        """Determine if a statement should be accepted as fact by thresholding."""
        return statement_confidence >= self.threshold_accept_as_fact


# Small example usage when run standalone
if __name__ == "__main__":
    from services.language_understanding import LanguageUnderstanding
    from services.learning_system import LearningSystem

    lu = LanguageUnderstanding()
    ls = LearningSystem(base_path=".")
    ce = CognitiveEngine(language_understanding=lu, learning_system=ls)

    q = "I'm feeling really anxious about school tomorrow"
    trace = ce.decide(q, user="hailey", profile={"display_name": "Hailey"})
    print("Decision Trace:\n", trace)
