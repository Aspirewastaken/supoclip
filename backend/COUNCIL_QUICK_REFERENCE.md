# Council System Quick Reference

**5-Model AI Council for Clip Selection**

---

## Usage

```python
from src.council import run_council_analysis, calculate_target_clips

# Run council analysis
result = await run_council_analysis(
    transcript="[00:00] Video content here...",
    video_duration=1800.0,  # 30 minutes
    user_notes="Focus on technical insights"
)

# Access results
print(f"Target clips: {result.target_clips}")  # 250 for 30min video
print(f"Models analyzed: {len(result.model_analyses)}")  # 5
print(f"Selected clips: {len(result.final_candidates)}")
print(f"Consensus level: {result.consensus_level:.2f}")  # 0.0-1.0
```

---

## Council Members (5 Models)

1. **Claude Sonnet 4.5** - `anthropic/claude-sonnet-4-20250514`
2. **Claude Opus 4.1** - `anthropic/claude-opus-4-20250514`
3. **GPT-4 Turbo** - `openai/gpt-4-turbo-preview`
4. **Gemini 2.5 Pro** - `google/gemini-pro-1.5`
5. **DeepSeek Chat** - `deepseek/deepseek-chat`

---

## Adaptive Clip Targeting

| Video Duration | Target Clips |
|----------------|--------------|
| 0-15 minutes   | 50 clips     |
| 15-90 minutes  | 250 clips    |
| 90+ minutes    | 500 clips    |

```python
calculate_target_clips(600)   # 10 min → 50 clips
calculate_target_clips(2700)  # 45 min → 250 clips
calculate_target_clips(7200)  # 2 hours → 500 clips
```

---

## Process Flow

### Phase 1: Independent Analysis
- All 5 models analyze transcript independently (parallel)
- Each model identifies engaging moments
- Models propose candidates with:
  - `start_time`, `end_time`, `duration`
  - `title`, `reasoning`
  - `engagement_score` (0-10)
  - `category` (action/story/emotional/quotable/reaction)

### Phase 2: Cross-Voting
- All candidates collected from Phase 1
- Deduplication (5-second threshold, keep highest engagement)
- Top 50% by engagement score go to voting
- All 5 models vote YES/NO on each candidate with confidence (0-1)
- Votes aggregated

### Phase 3: Final Selection
- Sort by: (1) YES votes, (2) confidence
- Select top N clips (N = target_clips)
- Calculate consensus level (average YES votes / 5)

---

## Data Models

### ClipCandidate
```python
ClipCandidate(
    start_time="1:30",      # MM:SS format
    end_time="2:00",        # MM:SS format
    duration=30.0,          # Seconds
    title="Key insight",    # Brief description
    reasoning="Why interesting",
    engagement_score=8.5,   # 0-10 (validated)
    category="story"        # Content type
)
```

### CouncilDeliberation (Result)
```python
{
    "video_duration": 1800.0,
    "target_clips": 250,
    "model_analyses": [...],      # 5 analyses
    "final_candidates": [...],    # Selected clips
    "consensus_level": 0.85       # 0-1 (85% agreement)
}
```

---

## Key Configuration

### Environment Variables
```bash
OPENROUTER_API_KEY=your_key_here
OPENROUTER_REFERER=http://localhost:3000  # Optional
```

### Deduplication Threshold
**Default:** 5 seconds
- Clips starting within 5 seconds of each other are considered duplicates
- Higher engagement score wins

### Voting Optimization
**Default:** Top 50% of candidates
- Only candidates in top half by engagement score are voted on
- Reduces API calls while maintaining quality

---

## Common Patterns

### Check Consensus Level
```python
result = await run_council_analysis(...)

if result.consensus_level > 0.8:
    print("High agreement among models")
elif result.consensus_level > 0.6:
    print("Moderate agreement")
else:
    print("Low agreement - diverse opinions")
```

### Access Individual Model Opinions
```python
for analysis in result.model_analyses:
    print(f"{analysis.model_name}: {len(analysis.candidates)} candidates")
    print(f"  Assessment: {analysis.overall_assessment}")
    print(f"  Recommended: {analysis.recommended_total_clips} clips")
```

### Filter by Category
```python
final_clips = result.final_candidates
action_clips = [c for c in final_clips if c.category == "action"]
story_clips = [c for c in final_clips if c.category == "story"]
emotional_clips = [c for c in final_clips if c.category == "emotional"]
```

---

## Error Handling

The system is designed to be resilient:

- **Model Failures:** If a model fails, others continue
- **JSON Parsing Errors:** Invalid responses are logged and skipped
- **Invalid Timestamps:** Clips with `end_time <= start_time` are filtered
- **Empty Results:** System handles zero candidates gracefully

```python
try:
    result = await run_council_analysis(...)
except Exception as e:
    logger.error(f"Council analysis failed: {e}")
    # Fall back to single-model or previous version
```

---

## Performance

### Typical Execution Times
- **Phase 1 (5 models):** 15-30 seconds (parallel)
- **Phase 2 (voting):** 10-20 seconds (parallel)
- **Deduplication:** <1 second
- **Total:** ~25-50 seconds for full analysis

### Optimization Tips
1. Use appropriate `video_duration` for accurate targeting
2. Provide clear `user_notes` for better model alignment
3. Cache results if re-running with same transcript
4. Monitor consensus levels to identify controversial clips

---

## Testing

```bash
# Run all council tests
pytest tests/unit/test_council_deliberation.py -v

# Run specific test class
pytest tests/unit/test_council_deliberation.py::TestEdgeCases -v

# With coverage
pytest tests/unit/test_council_deliberation.py --cov=src.council
```

---

## Debugging

### Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('src.council')
logger.setLevel(logging.DEBUG)
```

### Log Output Example
```
🎯 Video duration: 45.0 min → Target clips: 250
📊 Phase 1: Independent analysis by 5 council members
✅ Claude Sonnet 4.5: 52 candidates
✅ Claude Opus 4.1: 48 candidates
✅ GPT-4 Turbo: 55 candidates
✅ Gemini 2.5 Pro: 50 candidates
✅ DeepSeek Chat: 47 candidates
Total candidates from all models: 252
After deduplication: 187 candidates
🗳️  Phase 2: Council voting on candidates
Voting on top 94 candidates
✅ Claude Sonnet 4.5: Voted on 94 candidates
✅ Claude Opus 4.1: Voted on 94 candidates
✅ GPT-4 Turbo: Voted on 94 candidates
✅ Gemini 2.5 Pro: Voted on 94 candidates
✅ DeepSeek Chat: Voted on 94 candidates
✅ Phase 3: Selecting final clips
✅ Selected 250 final clips
Average YES votes for selected clips: 4.2 / 5
```

---

## Files

### Source Code
- `/home/user/supoclip/backend/src/council/deliberation.py` - Main logic (450 lines)
- `/home/user/supoclip/backend/src/council/models.py` - Data models (62 lines)
- `/home/user/supoclip/backend/src/council/__init__.py` - Exports (27 lines)

### Tests
- `/home/user/supoclip/backend/tests/unit/test_council_deliberation.py` - Tests (988 lines)

### Documentation
- `/home/user/supoclip/backend/COUNCIL_VALIDATION_REPORT.md` - Validation details
- `/home/user/supoclip/backend/COUNCIL_TEST_SUMMARY.md` - Test documentation
- `/home/user/supoclip/backend/COUNCIL_QUICK_REFERENCE.md` - This file

---

## API Reference

### Main Functions

#### `run_council_analysis(transcript, video_duration, user_notes="")`
Run full 3-phase council analysis.

**Returns:** `CouncilDeliberation`

#### `calculate_target_clips(video_duration_seconds)`
Calculate target clip count based on duration.

**Returns:** `int` (50, 250, or 500)

#### `deduplicate_candidates(candidates)`
Remove clips within 5 seconds of each other.

**Returns:** `List[ClipCandidate]`

#### `select_final_clips(voted_candidates, target_clips)`
Select top clips by votes and confidence.

**Returns:** `List[ClipCandidate]`

#### `calculate_consensus(voted_candidates, final_candidates)`
Calculate agreement level (0-1).

**Returns:** `float`

---

## Best Practices

1. **Always await:** All main functions are async
2. **Handle failures:** Individual model failures don't stop the process
3. **Monitor consensus:** Low consensus may indicate ambiguous content
4. **Use user_notes:** Clear instructions improve model alignment
5. **Cache wisely:** Re-running with same transcript is wasteful
6. **Test edge cases:** Use provided test suite as examples

---

## Support

- **Validation Report:** See `COUNCIL_VALIDATION_REPORT.md`
- **Test Details:** See `COUNCIL_TEST_SUMMARY.md`
- **Source Code:** See `src/council/` directory
- **Tests:** See `tests/unit/test_council_deliberation.py`

---

**Quick Reference Version:** 1.0.0
**Last Updated:** 2025-11-10
**Status:** Production Ready ✅
