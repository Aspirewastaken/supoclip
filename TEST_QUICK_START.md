# Testing Quick Start Guide

Quick reference for running tests in SupoClip.

## Backend Tests (Python/pytest)

### Setup
```bash
cd backend
uv sync
source .venv/bin/activate
```

### Run Tests
```bash
# All tests
pytest

# Unit tests only (fast)
pytest tests/unit -v

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_temporal_variations.py -v

# Watch mode (install pytest-watch first)
ptw
```

### Test Markers
```bash
pytest -m "not requires_api"      # Skip API tests
pytest -m "not requires_video"    # Skip video tests
pytest -m "not slow"              # Skip slow tests
```

## Frontend Tests (Vitest)

### Setup
```bash
cd frontend
npm install
```

### Run Tests
```bash
# All tests (watch mode)
npm test

# Run once
npm test -- --run

# With UI
npm run test:ui

# With coverage
npm run test:coverage

# Specific test file
npm test -- tests/components/button.test.tsx
```

## Test Structure

### Backend (`backend/tests/`)
```
tests/
├── conftest.py                          # Shared fixtures
├── unit/                                # Unit tests
│   ├── test_temporal_variations.py      # Temporal variations tests
│   ├── test_canvas_renderer.py          # Canvas rendering tests
│   ├── test_music_swapper.py            # Music swapper tests
│   └── test_council_deliberation.py     # Council deliberation tests
├── integration/                         # Integration tests
└── fixtures/                            # Test data
```

### Frontend (`frontend/tests/`)
```
tests/
├── setup.ts                    # Test configuration
├── components/                 # Component tests
│   ├── button.test.tsx
│   └── processing-animation.test.tsx
├── utils/                      # Utility tests
│   └── format.test.ts
└── hooks/                      # Hook tests
```

## Key Components Tested

### Backend
✅ **Temporal Variations** - Multi-duration clip generation
✅ **Canvas Renderer** - 3 rendering styles (original, flipped, blurry_bg)
✅ **Music Swapper** - Intelligent music selection with pool management
✅ **Council Deliberation** - 5-model AI consensus system

### Frontend
✅ **Button Component** - All variants and sizes
✅ **Processing Animation** - All states (queued, transcribing, analyzing, rendering, complete, error)
✅ **Utility Functions** - Time formatting, timestamp parsing

## CI/CD

Tests run automatically on:
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

**Workflow:** `.github/workflows/test.yml`

**Matrix:**
- Backend: Python 3.11, 3.12
- Frontend: Node 20.x, 22.x

## Coverage Targets

- **Backend:** 80%+ (core components)
- **Frontend:** 70%+ (components and utilities)

## Common Commands

### Backend
```bash
# Install test dependencies
uv pip install pytest pytest-asyncio pytest-cov pytest-mock httpx faker

# Run with verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests only
pytest --lf
```

### Frontend
```bash
# Install test dependencies (included in package.json)
npm install

# Run in different modes
npm test                    # Watch mode
npm test -- --run          # Run once
npm test -- --coverage     # With coverage
npm test -- --ui           # Interactive UI

# Filter tests
npm test -- --grep "Button"
npm test -- tests/components/
```

## Documentation

For detailed information, see:
- **TESTING.md** - Complete testing guide
- **pytest.ini** - Backend pytest configuration
- **vitest.config.ts** - Frontend Vitest configuration
- **backend/tests/conftest.py** - Shared test fixtures

## Tips

1. **Run tests before committing** - Catch issues early
2. **Write tests for new features** - Maintain coverage
3. **Use watch mode during development** - Immediate feedback
4. **Check coverage reports** - Identify gaps
5. **Mock external dependencies** - Keep tests fast and reliable
