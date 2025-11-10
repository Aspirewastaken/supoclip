# Testing Infrastructure

This document describes the comprehensive testing setup for SupoClip, including backend (Python/pytest) and frontend (TypeScript/Vitest) tests.

## Overview

- **Backend**: Python tests using pytest with async support
- **Frontend**: TypeScript tests using Vitest and React Testing Library
- **CI/CD**: GitHub Actions workflow for automated testing

## Backend Testing (Python/pytest)

### Directory Structure

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── unit/                    # Unit tests
│   │   ├── __init__.py
│   │   ├── test_temporal_variations.py
│   │   ├── test_canvas_renderer.py
│   │   ├── test_music_swapper.py
│   │   └── test_council_deliberation.py
│   ├── integration/             # Integration tests
│   │   └── __init__.py
│   └── fixtures/                # Test data
│       └── __init__.py
├── pytest.ini                   # Pytest configuration
└── pyproject.toml              # Dependencies including test libraries
```

### Running Backend Tests

#### Setup

```bash
cd backend

# Install dependencies (including test dependencies)
uv sync
uv pip install pytest pytest-asyncio pytest-cov pytest-mock httpx faker

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

#### Run All Tests

```bash
pytest
```

#### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit -v

# Integration tests only
pytest tests/integration -v

# Tests with specific markers
pytest -m "not requires_api"      # Skip tests needing API keys
pytest -m "not requires_video"    # Skip video processing tests
pytest -m "not slow"              # Skip slow tests
```

#### Run Specific Test Files

```bash
# Single test file
pytest tests/unit/test_temporal_variations.py -v

# Single test class
pytest tests/unit/test_temporal_variations.py::TestTemporalVariations -v

# Single test function
pytest tests/unit/test_temporal_variations.py::TestTemporalVariations::test_generate_base_variation -v
```

#### Coverage Reports

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View HTML coverage report
open htmlcov/index.html  # macOS
# xdg-open htmlcov/index.html  # Linux
# start htmlcov/index.html  # Windows

# Terminal coverage report
pytest --cov=src --cov-report=term-missing
```

#### Watch Mode (Run tests on file changes)

```bash
# Install pytest-watch
pip install pytest-watch

# Run in watch mode
ptw
```

### Test Markers

Available pytest markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (may need services)
- `@pytest.mark.slow` - Slow tests (video processing, AI calls)
- `@pytest.mark.requires_api` - Tests requiring API keys
- `@pytest.mark.requires_ffmpeg` - Tests requiring ffmpeg
- `@pytest.mark.requires_video` - Tests requiring video files

### Key Test Fixtures

Available in `conftest.py`:

- `sample_transcript` - Mock video transcript
- `sample_transcript_segments` - Mock transcript segments
- `sample_video_duration` - Sample video duration values
- `temp_video_file` - Temporary test video file
- `temp_vertical_video_file` - Temporary vertical video
- `sample_music_library` - Mock music library data
- `sample_frame` - NumPy array representing a video frame
- `mock_openrouter_response` - Mock for AI API calls

### Example Test

```python
import pytest
from src.variations.temporal import generate_temporal_variations

def test_generate_base_variation():
    """Test that base variation matches original duration."""
    variations = generate_temporal_variations(
        base_start=30.0,
        base_end=50.0,
        video_duration=300.0,
        include_frame_offset=False
    )

    assert len(variations) == 3
    base = variations[0]
    assert base.type == 'base'
    assert base.duration == 20.0
```

## Frontend Testing (Vitest)

### Directory Structure

```
frontend/
├── tests/
│   ├── setup.ts                # Test setup and global mocks
│   ├── components/             # Component tests
│   │   ├── button.test.tsx
│   │   └── processing-animation.test.tsx
│   ├── utils/                  # Utility function tests
│   │   └── format.test.ts
│   └── hooks/                  # Custom hook tests
├── vitest.config.ts            # Vitest configuration
└── package.json                # Test scripts
```

### Running Frontend Tests

#### Setup

```bash
cd frontend

# Install dependencies
npm install

# Dependencies include:
# - vitest
# - @testing-library/react
# - @testing-library/jest-dom
# - @testing-library/user-event
# - @vitest/ui
# - @vitest/coverage-v8
```

#### Run Tests

```bash
# Run all tests
npm test

# Run tests in watch mode (default)
npm test

# Run tests once
npm test -- --run

# Run with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

#### Run Specific Tests

```bash
# Run specific test file
npm test -- tests/components/button.test.tsx

# Run tests matching pattern
npm test -- --grep "Button"

# Run only changed tests
npm test -- --changed
```

### Test Utilities

**React Testing Library queries:**

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Render component
render(<Button>Click me</Button>);

// Query by role (preferred)
const button = screen.getByRole('button', { name: /click me/i });

// Query by text
const text = screen.getByText('Hello');

// User interactions
const user = userEvent.setup();
await user.click(button);
await user.type(input, 'text');
```

### Example Component Test

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '@/components/ui/button';

describe('Button', () => {
  it('handles click events', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(<Button onClick={handleClick}>Click me</Button>);

    const button = screen.getByRole('button');
    await user.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Mocking

**Mock Next.js router:**

```typescript
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
  usePathname: () => '/',
}));
```

**Mock API calls:**

```typescript
import { vi } from 'vitest';

const mockFetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ data: 'test' }),
  })
);

global.fetch = mockFetch as any;
```

## Continuous Integration (CI)

### GitHub Actions Workflow

Location: `.github/workflows/test.yml`

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Jobs:**

1. **backend-tests** - Runs backend tests on Python 3.11 and 3.12
2. **frontend-tests** - Runs frontend tests on Node 20.x and 22.x
3. **lint** - Runs linting checks
4. **test-summary** - Aggregates results

### Running CI Locally

#### Backend CI Simulation

```bash
cd backend
source .venv/bin/activate
pytest tests/unit -v -m "not requires_api" --cov=src --cov-report=xml
pytest tests/integration -v --cov=src --cov-append --cov-report=xml
```

#### Frontend CI Simulation

```bash
cd frontend
npm ci
npm test -- --run --coverage
npm run lint
```

## Code Coverage

### Backend Coverage

Target: **80%+ coverage** for core components

```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# View coverage
open htmlcov/index.html
```

### Frontend Coverage

Target: **70%+ coverage** for components and utilities

```bash
# Generate coverage report
npm run test:coverage

# View coverage
open coverage/index.html
```

## Best Practices

### Backend Testing

1. **Use fixtures** - Leverage pytest fixtures for reusable test data
2. **Mock external services** - Mock API calls, database, ffmpeg
3. **Test edge cases** - Boundary conditions, error handling
4. **Async tests** - Use `@pytest.mark.asyncio` for async functions
5. **Parameterize** - Use `@pytest.mark.parametrize` for multiple test cases

### Frontend Testing

1. **Query by role** - Prefer `getByRole` over other queries
2. **User interactions** - Use `@testing-library/user-event` for realistic interactions
3. **Async testing** - Use `waitFor` for async state changes
4. **Mock sparingly** - Test real implementations when possible
5. **Accessibility** - Use semantic queries to ensure accessibility

### General

1. **Descriptive names** - Use clear, descriptive test names
2. **Arrange-Act-Assert** - Structure tests clearly
3. **One assertion per test** - Keep tests focused
4. **Fast tests** - Mock slow operations (video processing, AI)
5. **Clean up** - Use fixtures and cleanup functions

## Troubleshooting

### Common Issues

**Backend:**

```bash
# Module not found
# Solution: Ensure virtual environment is activated and dependencies installed
source .venv/bin/activate
uv sync

# ffmpeg not found (for video tests)
# Solution: Install ffmpeg
brew install ffmpeg  # macOS
sudo apt-get install ffmpeg  # Linux

# Tests hang on async code
# Solution: Check for missing await statements
```

**Frontend:**

```bash
# Vitest not found
# Solution: Install dependencies
npm install

# Module resolution errors
# Solution: Check tsconfig.json paths and vitest.config.ts aliases

# React 19 warnings
# Solution: Ensure @testing-library/react is v16+
```

## Adding New Tests

### Backend

1. Create test file in appropriate directory (`tests/unit/` or `tests/integration/`)
2. Import necessary fixtures from `conftest.py`
3. Add test markers if needed
4. Run tests to verify

```python
# tests/unit/test_new_feature.py
import pytest
from src.new_feature import new_function

def test_new_function():
    result = new_function(input_data)
    assert result == expected_output
```

### Frontend

1. Create test file next to component or in `tests/` directory
2. Import testing utilities
3. Write tests using React Testing Library
4. Run tests to verify

```typescript
// tests/components/new-component.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { NewComponent } from '@/components/new-component';

describe('NewComponent', () => {
  it('renders correctly', () => {
    render(<NewComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Best Practices](https://testingjavascript.com/)

## Maintenance

- **Update dependencies** regularly for security and features
- **Review coverage** reports to identify untested code
- **Refactor tests** as code evolves
- **Add tests** for bug fixes to prevent regressions
- **Monitor CI** performance and optimize slow tests
