# SupoClip Security Hardening Guide
**Quick Reference for Developers**

This guide provides step-by-step instructions to secure the SupoClip application.

---

## 🚀 Quick Start (5 Minutes)

### 1. Install Required Dependencies

```bash
cd backend
uv add python-magic redis aiofiles
```

### 2. Update main.py - Replace CORS

**Before**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ INSECURE
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**After**:
```python
from .middleware import SecurityHeadersMiddleware, CORSSecurityMiddleware

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSSecurityMiddleware,
    allowed_origins=[
        "http://localhost:3000",
        "https://supoclip.com",
        "https://app.supoclip.com"
    ]
)
```

### 3. Secure All Endpoints

Add authentication to every endpoint that accesses user data:

```python
from .middleware import get_current_user

@app.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    current_user: str = Depends(get_current_user),  # ✅ Add this line
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    task = await get_task_from_db(task_id)
    if task.user_id != current_user:
        raise HTTPException(403, "Not authorized")

    return task
```

### 4. Add Rate Limiting

```python
from .middleware import video_processing_rate_limit, api_rate_limit

@app.post("/start")
async def start_task(
    request: Request,
    current_user: str = Depends(get_current_user)
):
    await video_processing_rate_limit(request, current_user)  # ✅ Add this
    # ... rest of endpoint
```

### 5. Secure File Uploads

```python
from .utils.file_validation import FileValidator

@app.post("/upload")
async def upload_video(
    video: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    # Validate file
    is_valid, sanitized_filename = await FileValidator.validate_upload(video)  # ✅ Add this

    # Continue with processing...
```

---

## 📋 Endpoint Security Checklist

For **EVERY** endpoint, check these boxes:

- [ ] Has authentication (`Depends(get_current_user)`)
- [ ] Has rate limiting (for non-public endpoints)
- [ ] Verifies resource ownership (for user resources)
- [ ] Validates all inputs
- [ ] Logs security events
- [ ] Returns appropriate error codes (401, 403, 429)

---

## 🔐 Authentication Pattern

### Standard Pattern for All Endpoints

```python
from fastapi import Depends, HTTPException
from .middleware import get_current_user, verify_resource_ownership

@app.get("/resource/{resource_id}")
async def get_resource(
    resource_id: str,
    current_user: str = Depends(get_current_user),  # 1. Authenticate
    db: AsyncSession = Depends(get_db)
):
    # 2. Get resource
    resource = await db.execute(
        text("SELECT * FROM resources WHERE id = :id"),
        {"id": resource_id}
    )
    resource = resource.fetchone()

    if not resource:
        raise HTTPException(404, "Resource not found")

    # 3. Verify ownership
    if resource.user_id != current_user:
        raise HTTPException(403, "Not authorized to access this resource")

    # 4. Return data
    return {"resource": dict(resource._mapping)}
```

### Public Endpoints (No Auth Required)

Only these endpoints should be public:
- `GET /` (API root)
- `GET /health/db` (health check)
- `GET /docs` (API documentation)
- `GET /fonts` (public resources)
- `GET /transitions` (public resources)

All other endpoints MUST require authentication.

---

## 🛡️ Rate Limiting Examples

### Video Processing (Expensive Operations)

```python
from .middleware import video_processing_rate_limit

@app.post("/start")
@app.post("/start-with-progress")
async def process_video(
    request: Request,
    current_user: str = Depends(get_current_user)
):
    # Rate limit: 10 requests per hour
    await video_processing_rate_limit(request, current_user)

    # ... process video
```

### Standard API Endpoints

```python
from .middleware import api_rate_limit

@app.get("/tasks/")
async def list_tasks(
    request: Request,
    current_user: str = Depends(get_current_user)
):
    # Rate limit: 100 requests per minute
    await api_rate_limit(request, current_user)

    # ... return tasks
```

### Custom Rate Limits

```python
from .middleware import rate_limit_dependency

@app.post("/expensive-operation")
async def expensive_op(request: Request, current_user: str = Depends(get_current_user)):
    # Custom: 5 requests per 10 minutes
    await rate_limit_dependency(
        request=request,
        user_id=current_user,
        max_requests=5,
        window_seconds=600
    )

    # ... perform operation
```

---

## 📁 File Upload Security

### Complete Validation Example

```python
from fastapi import UploadFile, File
from .utils.file_validation import FileValidator
from .middleware import get_current_user, api_rate_limit
import aiofiles
import uuid
from pathlib import Path

@app.post("/upload")
async def upload_video(
    request: Request,
    video: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    # 1. Rate limit
    await api_rate_limit(request, current_user)

    # 2. Validate file (type, size, content)
    is_valid, sanitized_filename = await FileValidator.validate_upload(video)

    # 3. Generate secure filename
    file_extension = Path(sanitized_filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # 4. Save to user-specific directory
    user_dir = Path(config.temp_dir) / "uploads" / current_user
    user_dir.mkdir(parents=True, exist_ok=True)

    video_path = user_dir / unique_filename

    # 5. Write file securely
    async with aiofiles.open(video_path, 'wb') as f:
        content = await video.read()
        await f.write(content)

    # 6. Log upload
    logger.info(f"User {current_user} uploaded {sanitized_filename} ({len(content)} bytes)")

    return {
        "message": "Upload successful",
        "video_path": str(video_path),
        "size": len(content)
    }
```

---

## 🔒 Ownership Verification Pattern

### Manual Verification

```python
@app.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get task
    result = await db.execute(
        text("SELECT user_id FROM tasks WHERE id = :id"),
        {"id": task_id}
    )
    task = result.fetchone()

    if not task:
        raise HTTPException(404, "Task not found")

    # Verify ownership
    if task.user_id != current_user:
        logger.warning(f"User {current_user} tried to delete task owned by {task.user_id}")
        raise HTTPException(403, "Not authorized to delete this task")

    # Proceed with deletion
    await db.execute(text("DELETE FROM tasks WHERE id = :id"), {"id": task_id})
    await db.commit()

    return {"message": "Task deleted"}
```

### Using Helper Function

```python
from .middleware import verify_resource_ownership

@app.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get task
    task = await get_task_from_db(task_id)

    # Verify ownership (raises 403 if not owner)
    await verify_resource_ownership(task.user_id, current_user)

    # Proceed with deletion
    await delete_task_from_db(task_id)

    return {"message": "Task deleted"}
```

---

## 🌐 CORS Configuration

### Development (Localhost)

```python
app.add_middleware(
    CORSSecurityMiddleware,
    allowed_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]
)
```

### Production

```python
import os

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
# Example: ALLOWED_ORIGINS="https://supoclip.com,https://app.supoclip.com"

app.add_middleware(
    CORSSecurityMiddleware,
    allowed_origins=ALLOWED_ORIGINS
)
```

### Testing CORS

```bash
# Should succeed (allowed origin)
curl -H "Origin: http://localhost:3000" http://localhost:8000/tasks/

# Should fail (disallowed origin)
curl -H "Origin: https://evil.com" http://localhost:8000/tasks/
```

---

## 🚨 Error Handling Best Practices

### Security-Aware Error Messages

**❌ Bad** (reveals too much):
```python
if not user:
    raise HTTPException(404, f"User {user_id} not found in database")
```

**✅ Good** (generic message):
```python
if not user:
    raise HTTPException(401, "Invalid authentication credentials")
```

### Standard Error Responses

```python
# Authentication failure
raise HTTPException(
    status_code=401,
    detail="Authentication required",
    headers={"WWW-Authenticate": "Bearer"}
)

# Authorization failure
raise HTTPException(
    status_code=403,
    detail="Not authorized to access this resource"
)

# Rate limit exceeded
raise HTTPException(
    status_code=429,
    detail="Rate limit exceeded",
    headers={
        "Retry-After": "3600",
        "X-RateLimit-Limit": "10",
        "X-RateLimit-Remaining": "0"
    }
)

# Resource not found (no ownership hint)
raise HTTPException(
    status_code=404,
    detail="Resource not found"
)

# Validation error
raise HTTPException(
    status_code=400,
    detail="Invalid input: field 'email' is required"
)
```

---

## 📊 Logging Security Events

### What to Log

```python
import logging
logger = logging.getLogger(__name__)

# ✅ Log authentication events
logger.info(f"User {user_id} authenticated successfully")
logger.warning(f"Authentication failed: Invalid user_id {user_id}")

# ✅ Log authorization failures
logger.warning(f"User {current_user} attempted to access resource owned by {owner_id}")

# ✅ Log rate limit hits
logger.warning(f"Rate limit exceeded for user {user_id} on {endpoint}")

# ✅ Log file uploads
logger.info(f"User {user_id} uploaded {filename} ({size} bytes)")

# ✅ Log suspicious activity
logger.warning(f"Path traversal attempt detected: {filename}")
logger.warning(f"Invalid MIME type detected: {mime_type}")

# ❌ Don't log sensitive data
logger.info(f"User logged in with password: {password}")  # NEVER DO THIS
```

### Log Levels

- `INFO`: Normal security events (logins, uploads)
- `WARNING`: Suspicious activity (auth failures, rate limits)
- `ERROR`: Security errors (validation failures)
- `CRITICAL`: Security incidents (multiple auth failures, attacks)

---

## 🧪 Testing Security

### Unit Tests

```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient

def test_endpoint_requires_auth(client: TestClient):
    """Test that endpoint requires authentication"""
    response = client.get("/tasks/test-id")
    assert response.status_code == 401
    assert "authentication" in response.json()["detail"].lower()

def test_endpoint_with_valid_auth(client: TestClient):
    """Test endpoint with valid authentication"""
    response = client.get(
        "/tasks/test-id",
        headers={"user_id": "valid-user-id"}
    )
    assert response.status_code in [200, 404]  # 404 if task doesn't exist

def test_ownership_verification(client: TestClient):
    """Test that users can only access their own resources"""
    response = client.get(
        "/tasks/other-user-task",
        headers={"user_id": "user1"}
    )
    assert response.status_code == 403

def test_rate_limiting(client: TestClient):
    """Test rate limiting is enforced"""
    for i in range(11):
        response = client.post(
            "/start",
            json={"source": {"url": "test"}},
            headers={"user_id": "test-user"}
        )

    # 11th request should be rate limited
    assert response.status_code == 429
```

### Manual Testing Checklist

```bash
# ✅ Test authentication
curl http://localhost:8000/tasks/test-id
# Expected: 401 Unauthorized

# ✅ Test CORS
curl -H "Origin: https://evil.com" http://localhost:8000/tasks/
# Expected: No Access-Control-Allow-Origin header

# ✅ Test rate limiting
for i in {1..11}; do
  curl -H "user_id: test" http://localhost:8000/start
done
# Expected: 11th request returns 429

# ✅ Test file validation
curl -F "video=@test.exe" http://localhost:8000/upload
# Expected: 400 File type not allowed

# ✅ Test security headers
curl -I http://localhost:8000/
# Expected: X-Frame-Options, CSP, HSTS, etc.

# ✅ Test ownership
curl -H "user_id: user1" http://localhost:8000/tasks/user2-task-id
# Expected: 403 Forbidden
```

---

## 📦 Dependencies

### Required Security Packages

```bash
# Add to backend/pyproject.toml
uv add python-magic  # MIME type detection
uv add redis        # Rate limiting
uv add aiofiles     # Async file operations
```

### Optional Security Tools

```bash
# Development tools
pip install bandit         # Security linter
pip install safety         # Dependency vulnerability scanner
pip install pytest-security  # Security testing

# Run security checks
bandit -r backend/src/
safety check
```

---

## 🔧 Environment Variables

### Required Security Configuration

```bash
# .env file
ALLOWED_ORIGINS=https://supoclip.com,https://app.supoclip.com
REDIS_HOST=localhost
REDIS_PORT=6379
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here

# Optional
RATE_LIMIT_ENABLED=true
MAX_FILE_SIZE_MB=500
SESSION_SECRET=your-random-secret-here
```

---

## 🚀 Deployment Checklist

Before deploying to production:

- [ ] All endpoints have authentication
- [ ] Rate limiting is enabled and configured
- [ ] CORS is configured with specific origins (no wildcards)
- [ ] Security headers middleware is enabled
- [ ] File upload validation is implemented
- [ ] HTTPS is enforced (redirect HTTP → HTTPS)
- [ ] Secrets are stored in environment variables
- [ ] Database connections use SSL/TLS
- [ ] Redis connections use TLS (if remote)
- [ ] Error messages don't leak sensitive information
- [ ] Logging is configured and monitored
- [ ] Security tests pass
- [ ] Dependency vulnerabilities are resolved
- [ ] Stripe webhook signature verification is enabled
- [ ] Static files require authentication
- [ ] Admin endpoints have extra protection

---

## 📞 Support

**Questions?** Contact: security@supoclip.com

**Found a vulnerability?** Report to: security@supoclip.com

**Documentation**: See `SECURITY_AUDIT_REPORT.md` for detailed findings.
