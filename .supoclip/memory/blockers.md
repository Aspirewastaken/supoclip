# Blockers

**Current Blockers**: 2 active blockers

## Active Blockers

### BLOCKER 1: MLX Transcription Server Not Available
- **Task**: Phase 1A, Task 4 - Start MLX transcription server on port 5001
- **Issue**: MLX server not running on localhost:5001
- **Root Cause**: MLX (Apple's ML framework) requires macOS with Apple Silicon. Current environment is Linux.
- **Impact**: Cannot complete Phase 1A Task 4, blocking Phase 1C (MLX Integration)
- **Possible Solutions**:
  1. Install and run MLX-compatible transcription server (requires macOS/Apple Silicon)
  2. Use AssemblyAI API instead (already integrated as fallback in transcription_utils.py)
  3. Use OpenAI Whisper API
  4. Run local Whisper model via whisper.cpp or faster-whisper
- **Recommended**: Use AssemblyAI as primary (requires ASSEMBLY_AI_API_KEY env var)
- **Status**: BLOCKED - Awaiting decision on transcription service

### BLOCKER 2: Backend Import Errors from Previous Session
- **Task**: Phase 1B, Task 10 - Test with curl on actual video file
- **Issue**: FastAPI server fails to start due to import errors
- **Root Cause**: Previous 30-agent session left incomplete/incompatible code
- **Errors Found & Fixed**:
  1. ✅ Fixed: ValidationError class missing in custom_exceptions.py
  2. ✅ Fixed: CalendarCredential.metadata conflicts with SQLAlchemy reserved name
  3. ⚠️ REMAINING: ImportError - `get_most_relevant_parts_by_transcript` missing from src/ai/__init__.py
- **Impact**: Cannot start FastAPI server to test endpoints with curl
- **Status**: PARTIALLY BLOCKED - 2 bugs fixed, 1 remaining

## Potential Blockers to Watch For

### Phase 1A
- PostgreSQL not installed or not running
- MLX transcription server not available on host
- Port conflicts with other services

### Phase 1B
- Missing API keys (OPENROUTER_API_KEY)
- Database connection failures
- Missing Python dependencies

### Phase 1C
- MLX server connectivity issues
- Transcription API rate limits

---

**Last Updated**: 2025-11-10 (Session Start)
