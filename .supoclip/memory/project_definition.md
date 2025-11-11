# SupoClip Project Definition

## Vision
Open-source alternative to OpusClip - AI-powered video clipping tool that transforms long-form content into viral short clips.

## Core System Architecture

### Phase 1: Council System (50 tasks)
5-model AI council votes on transcript segments to identify viral moments. Generates 50-500 clips depending on video length.

### Phase 2: Premiere Integration (20 tasks)
Export clips to Premiere Pro XML format. Wes edits clips. Re-upload edited clips to trigger Phase 3.

### Phase 3: Matrix Processing (35 tasks)
For each base clip, generate 9 variations:
- 3 temporal variations (base, +4s, +35s)
- 3 canvas styles (original, flipped, blurry_bg)
- Random 5-10 frame offset per variation

### Phase 4: Variation Generation (30 tasks)
Apply finishing touches to all variations:
- Account-specific watermarks (green screen overlay)
- Title cards (TT³ bubble top OR AdLab Standard bottom)
- Music (40-song pool, intelligent selection)
- Captions (Proxima Nova Sans, 135, centered, 11 chars/line)

### Phase 5: Distribution (25 tasks)
Posting system with:
- Database tracking (17+ accounts)
- Posting Helper (screenshot → AI title generation)
- Calendar integration (5-min events)
- Upload queue with retry logic

## Key Technologies
- **Backend**: Python/FastAPI, PostgreSQL, Redis
- **Frontend**: Next.js 15, React 19, ShadCN UI
- **AI**: OpenRouter (5 models), Whisper (transcription)
- **Video**: FFmpeg, MoviePy
- **Auth**: Better Auth with Prisma

## Non-Negotiables
- NO 9:16 crop in base clips (preserve horizontal)
- NO captions/effects in base clips (clean cuts only)
- Council must use EXACTLY 5 models
- User notes guide AI analysis
- Adaptive targeting (50/250/500 clips based on duration)

## Success Criteria
- 175 tasks completed
- All 5 phases operational
- System generates 500 clips + 4,500 variations in <8 hours
- Wes workflow validated in Premiere
- Distribution system tracks all posts

## Total Scope
**175 tasks** across 5 phases = 10-12 days estimated completion

---

**This file never changes. It's the source of truth.**
