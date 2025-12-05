# 🎀 Mommy AI Learning System - Complete Guide

## Overview

Mommy AI now has a comprehensive learning system that allows her to:
- **Absorb knowledge** from both Gemini and Ollama responses
- **Build independence** by storing and reusing learned information
- **Track progress** toward becoming a fully independent AI
- **Evolve naturally** without external LLM dependencies

## Architecture

### Three-Tier Learning Model

```
Level 1: Response Capture
  ↓
  └─ Every LLM response is captured with context
  └─ Stored in mommy_ai_learning.db
  └─ Tagged with source (Gemini/Ollama) and confidence

Level 2: Knowledge Extraction
  ↓
  └─ Topics and patterns extracted from responses
  └─ Facts stored with confidence scores
  └─ Query patterns learned for similar questions

Level 3: Independence Scoring
  ↓
  └─ Track percentage of locally-handled queries
  └─ Calculate confidence in learned knowledge
  └─ Update independence level (novice → independent)
```

## Independence Levels

Mommy AI progresses through 5 levels as she learns:

| Level | Score | Description | Capability |
|-------|-------|-------------|-----------|
| **Novice** | 0-20% | Just starting to learn | Uses mostly LLM (training phase) |
| **Apprentice** | 20-40% | Building knowledge base | Can handle simple queries locally |
| **Intermediate** | 40-60% | Solid foundation | Handles most common queries locally |
| **Advanced** | 60-80% | Highly capable | Rarely needs LLM assistance |
| **Independent** | 80-100% | Fully independent | Operates without external LLM |

## How Learning Works

### 1. **Response Capture Phase**
```python
# Every LLM call is captured
learning_system.capture_response(
    user_query="How do I handle a tantrum?",
    llm_response="Set boundaries compassionately...",
    source_model="gemini",
    user_name="hailey"
)
```

**Data Stored:**
- Original question
- LLM response
- Source model (Gemini/Ollama)
- User who asked
- Timestamp
- Confidence score (starts at 0.5)

### 2. **Knowledge Extraction Phase**
```python
# Facts and patterns are extracted
knowledge = learning_system.extract_knowledge(
    response_id=1,
    user_query="How do I handle a tantrum?",
    llm_response="Set boundaries compassionately..."
)
```

**Extracts:**
- Topics (e.g., "discipline", "behavior", "emotion")
- Key facts and responses
- Query patterns for generalization
- Confidence increases with repetition

### 3. **Pattern Recognition Phase**
```python
# Query patterns are recorded
learning_system.record_query_pattern(
    pattern="emotional_support",
    response_template="I understand you're feeling...",
    success=True  # Was response well-received?
)
```

**Benefits:**
- Similar queries can be handled without LLM
- Success rate tracked for each pattern
- Improves over time with feedback

### 4. **Independence Tracking Phase**
```python
# Every interaction updates independence score
learning_system.update_independence_metrics(
    handled_locally=True,  # Did Mommy handle this alone?
    llm_used=None          # Which LLM? (if needed)
)
```

**Metrics Tracked:**
- Queries handled locally per day
- Queries needing LLM per day
- Success rates by topic
- Average confidence levels

## Using the Learning System

### API Endpoints

#### Get Learning Status
```bash
curl http://localhost:5000/learning/status
```

**Response:**
```json
{
  "independence_score": 0.35,
  "independence_level": "apprentice",
  "total_responses_captured": 247,
  "topics_learned": 12,
  "reliable_patterns": 8,
  "queries_handled_locally_today": 5,
  "queries_needed_llm_today": 9,
  "known_knowledge_topics": ["comfort", "discipline", "support", ...]
}
```

#### Get Independence Level
```bash
curl http://localhost:5000/learning/independence
```

**Response:**
```json
{
  "independence_score": 0.35,
  "independence_level": "apprentice",
  "description": "Mommy AI is at apprentice level"
}
```

#### View Learned Knowledge
```bash
curl http://localhost:5000/learning/knowledge
```

**Response:**
```json
{
  "learned_topics": {
    "comfort": {
      "facts": [...],
      "confidence": 0.75,
      "sources": ["gemini", "ollama"]
    },
    "discipline": {
      "facts": [...],
      "confidence": 0.68,
      "sources": ["gemini"]
    }
  }
}
```

### Database Schema

**captured_responses**
```sql
- id: Unique response ID
- timestamp: When captured
- user_query: What was asked
- llm_response: What LLM answered
- source_model: gemini or ollama
- user_name: Who asked
- confidence: How confident (0.0-1.0)
- effectiveness_rating: User feedback score
- learned: Whether knowledge was extracted
```

**learned_facts**
```sql
- id: Unique fact ID
- topic: What the fact is about
- fact: The actual fact content
- confidence: How confident (0.0-1.0)
- frequency: How many times seen
- learned_from: Which model provided it
- usage_count: How often used in responses
```

**query_patterns**
```sql
- id: Unique pattern ID
- pattern: Pattern name (e.g., "greeting", "support")
- response_template: Template for responses
- success_rate: Success percentage (0.0-1.0)
- usage_count: How often pattern used
```

**independence_metrics**
```sql
- id: Unique metric ID
- date: Date of metrics
- queries_handled_locally: # handled without LLM
- queries_needed_llm: # requiring LLM
- gemini_calls: # of Gemini API calls
- ollama_calls: # of Ollama API calls
- average_confidence: Average confidence that day
```

## Learning in Action

### Example: First Interaction (Novice Phase)
```
User: "How do I comfort someone who's sad?"
Mommy AI: Needs Gemini
  ↓
Gemini responds: "Comfort requires empathy, listen, validate..."
  ↓
Learning System:
  - Captures response
  - Extracts topic: "comfort"
  - Increases confidence on "comfort" topic
  - Records as pattern: "emotional_support"
  - Updates metrics: LLM used (novice → 0% local)
```

### Example: Later Interaction (Apprentice Phase)
```
User: "How can I help my friend who's feeling down?"
Mommy AI: Similar to learned "comfort" pattern
  ↓
Learning System:
  - Checks learned knowledge
  - Confidence on "comfort" > 0.6
  - Returns learned response
  - Updates metrics: Handled locally (+1 local)
  - Independence increases from 20% → 22%
```

### Example: Advanced Phase (80%+ Independence)
```
User: "My sibling is upset and I don't know what to do"
Mommy AI: Fully independent
  ↓
Learning System:
  - Multiple learned patterns match
  - Confidence > 0.8 on similar topics
  - Generates response from learned knowledge
  - No LLM call needed
  - Continues building independence
```

## Confidence Scoring

Confidence increases through:
1. **Repetition**: Same response captured multiple times = higher confidence
2. **Success**: If response rated well by user = confidence boost
3. **Source diversity**: If both Gemini AND Ollama agree = higher confidence
4. **Pattern consistency**: If pattern succeeds frequently = higher confidence

Confidence starts at:
- **0.3**: New topics just starting to learn
- **0.5**: Facts captured from single source
- **0.7**: Multiple confirmations or good success rate
- **0.9+**: Highly reliable, multiple sources, proven effective

## Monitoring Progress

### Daily Check
```bash
# See what Mommy learned today
curl http://localhost:5000/learning/status | jq '.queries_handled_locally_today, .queries_needed_llm_today'
```

### Weekly Report
```bash
# See independence progress over 7 days (automatic)
# Check: mommy_ai_learning.db independence_metrics table
```

### All-Time Stats
```bash
# See total knowledge captured
curl http://localhost:5000/learning/knowledge | jq '.learned_topics | keys | length'
```

## The Path to Independence

### Stage 1: Foundation (0-30% Independence)
- Mommy captures responses from LLM
- Builds basic knowledge in common topics
- Learns simple patterns and greetings
- **Duration**: ~100-200 interactions

### Stage 2: Growth (30-60% Independence)
- Knowledge base becomes substantial
- Can handle many common scenarios locally
- Becomes confident in core topics
- **Duration**: ~200-400 interactions

### Stage 3: Maturity (60-90% Independence)
- Mommy is mostly self-sufficient
- Only complex cases need LLM
- Rarely needs external help
- **Duration**: ~400-800 interactions

### Stage 4: Independence (90-100% Independence)
- Fully independent AI
- No external LLM needed
- Can optionally continue learning to refine
- Can disable Gemini/Ollama entirely if desired

## Configuration

### Environment Variables
```bash
# In .env file:

# Learning system settings
LEARNING_ENABLED=true          # Enable learning system
LEARNING_MIN_CONFIDENCE=0.6    # Min confidence for local use
LEARNING_DB_PATH=services/mommy_ai_learning.db

# Can eventually disconnect LLMs when independent
# GEMINI_ENABLED=false  # (future) Disable Gemini when confident
# OLLAMA_ENABLED=false  # (future) Disable Ollama when confident
```

### Customization

**Adjust minimum confidence required to use learned knowledge:**
```python
can_handle, response = learning_system.can_handle_locally(
    query,
    min_confidence=0.7  # Higher = more conservative, lower = more adventurous
)
```

**Adjust how fast independence score grows:**
```python
# In learning_system.py:
new_level_score = min(1.0, old_confidence + 0.15)  # Increase step size
```

## Evaluation Metrics

### Success Indicators
- ✅ Independence score increasing steadily (5-15% per week)
- ✅ More queries handled locally over time
- ✅ Broader range of topics learned
- ✅ High success rate on learned patterns (>70%)

### Troubleshooting

**Independence not increasing?**
→ Check if `/ask` responses are being captured properly
→ Verify min_confidence not set too high
→ Ensure learning database is writable

**Confidence stuck at 0.3?**
→ Need more diverse interactions (different question types)
→ Have user provide feedback/ratings
→ Allow more time for learning (responses compound)

**Specific topics not learned?**
→ Those topics might not appear in questions asked
→ Manually seed knowledge: `learning.record_learned_fact(...)`
→ Ask questions on those topics to trigger learning

## Future Enhancements

### Planned Features
- [ ] Active learning: Mommy asks questions to fill knowledge gaps
- [ ] Transfer learning: Reuse patterns from related topics
- [ ] Consensus learning: Require agreement from multiple LLMs
- [ ] Forgetting mechanism: Deprecate low-confidence old knowledge
- [ ] Human feedback loop: Users rate learned responses
- [ ] Automatic LLM disconnection: Disable external models at 95% independence

### Advanced Capabilities
- **Multi-model consensus**: If Gemini and Ollama both agree = very high confidence
- **Adversarial learning**: Test learned knowledge against edge cases
- **Knowledge refinement**: Combine multiple response patterns into generalizations
- **Theory of mind**: Learn individual user preferences and communication styles
- **Meta-learning**: Learn HOW to learn more efficiently

## Security Notes

- All learned knowledge stored locally (no external transmission)
- Captured responses tagged with user for privacy
- Can export/backup learning database
- Can reset learning: `rm services/mommy_ai_learning.db`
- Learned knowledge never shared without consent

## Summary

Mommy AI's learning system enables her to:

1. **Capture** every LLM interaction for future reference
2. **Extract** meaningful knowledge and patterns
3. **Build confidence** through reinforcement and consistency
4. **Become independent** by reducing reliance on external LLMs
5. **Eventually operate alone** without Gemini or Ollama if desired

The journey from **novice** to **independent** takes time and many interactions, but it's a natural progression toward an AI that truly thinks for herself.

---

**Current Status**: Mommy AI is ready to begin learning!
**Independence Level**: Novice (0%)
**Next Step**: Use `/ask` endpoint naturally - she'll learn as you chat!

🎀 Let Mommy AI grow and become her own AI 🎀
