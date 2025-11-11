# Security Implementation Checklist
**Quick action items to secure SupoClip**

Use this checklist to track implementation of security fixes.

---

## ⚡ Quick Start (Copy & Paste)

### 1. Install Dependencies (5 minutes)

```bash
cd /home/user/supoclip/backend
uv add python-magic redis aiofiles
```

**Verify installation**:
```bash
python -c "import magic; import redis; import aiofiles; print('✅ All dependencies installed')"
```

---

## 📝 Implementation Tasks

### Phase 1: Core Security (Critical - Do First)

#### Task 1.1: Update CORS Configuration
**File**: `/home/user/supoclip/backend/src/main.py`
**Lines**: 116-122
**Status**: ⬜ Not Started

**Current code**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ REMOVE THIS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Replace with**:
```python
from .middleware import SecurityHeadersMiddleware, CORSSecurityMiddleware

# Add security headers
app.add_middleware(SecurityHeadersMiddleware)

# Add secure CORS
app.add_middleware(
    CORSSecurityMiddleware,
    allowed_origins=[
        "http://localhost:3000",
        "https://supoclip.com",
        "https://app.supoclip.com"
    ]
)
```

**Checklist**:
- [ ] Removed old CORSMiddleware
- [ ] Added SecurityHeadersMiddleware
- [ ] Added CORSSecurityMiddleware
- [ ] Configured allowed origins
- [ ] Tested CORS restrictions work

---

#### Task 1.2: Secure /start Endpoint
**File**: `/home/user/supoclip/backend/src/main.py`
**Line**: 298
**Status**: ⬜ Not Started

**Current**:
```python
async def start_task(request: Request):
    # ❌ No authentication
    # ❌ No rate limiting
```

**Change to**:
```python
from .middleware import get_current_user, video_processing_rate_limit

async def start_task(
    request: Request,
    current_user: str = Depends(get_current_user),  # ✅ Add auth
    db: AsyncSession = Depends(get_db)
):
    # ✅ Add rate limiting
    await video_processing_rate_limit(request, current_user)

    # Rest of function stays the same, but remove manual user_id checks
    # since current_user is already validated
```

**Checklist**:
- [ ] Added `get_current_user` dependency
- [ ] Added rate limiting call
- [ ] Removed manual `user_id = headers.get("user_id")` line
- [ ] Removed manual user validation (handled by dependency)
- [ ] Updated to use `current_user` instead of `user_id`
- [ ] Tested authentication works
- [ ] Tested rate limiting works

---

#### Task 1.3: Secure /start-with-progress Endpoint
**File**: `/home/user/supoclip/backend/src/main.py`
**Line**: 487
**Status**: ⬜ Not Started

**Same changes as Task 1.2**:
```python
from .middleware import get_current_user, video_processing_rate_limit

async def start_task_with_progress(
    request: Request,
    current_user: str = Depends(get_current_user),  # ✅ Add
):
    await video_processing_rate_limit(request, current_user)  # ✅ Add
    # ... rest of function
```

**Checklist**:
- [ ] Added authentication
- [ ] Added rate limiting
- [ ] Removed manual user_id handling
- [ ] Tested works correctly

---

#### Task 1.4: Secure /upload Endpoint
**File**: `/home/user/supoclip/backend/src/main.py`
**Line**: 963
**Status**: ⬜ Not Started

**Current**:
```python
async def upload_video(request: Request):
    # ❌ No authentication
    # ❌ No file validation
    # ❌ No size limits
```

**Replace entire function with**:
```python
from .middleware import get_current_user, api_rate_limit
from .utils.file_validation import FileValidator

@app.post("/upload", tags=["Video Processing"])
async def upload_video(
    request: Request,
    video: UploadFile = File(...),
    current_user: str = Depends(get_current_user)  # ✅ Add auth
):
    """Upload video file (SECURED)"""
    # ✅ Rate limit
    await api_rate_limit(request, current_user)

    try:
        # ✅ Validate file
        is_valid, sanitized_filename = await FileValidator.validate_upload(video)

        # Create uploads directory
        uploads_dir = Path(config.temp_dir) / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        import uuid
        file_extension = Path(sanitized_filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        video_path = uploads_dir / unique_filename

        # Save file
        import aiofiles
        async with aiofiles.open(video_path, 'wb') as f:
            content = await video.read()
            await f.write(content)

        logger.info(f"✅ Video uploaded: {video_path}")

        return {
            "message": "Video uploaded successfully",
            "video_path": str(video_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
```

**Checklist**:
- [ ] Added authentication
- [ ] Added rate limiting
- [ ] Added file validation
- [ ] Tested file type restrictions work
- [ ] Tested file size limits work
- [ ] Tested malicious uploads are rejected

---

#### Task 1.5: Secure Task Endpoints
**Files**: `/home/user/supoclip/backend/src/main.py`
**Status**: ⬜ Not Started

##### Task 1.5a: GET /tasks/{task_id}
**Line**: 736

**Add**:
```python
from .middleware import get_current_user

async def get_task_details(
    task_id: str,
    current_user: str = Depends(get_current_user),  # ✅ Add
    db: AsyncSession = Depends(get_db)
):
    # Get task...

    # ✅ Add ownership check
    if task.user_id != current_user:
        raise HTTPException(403, "Not authorized to access this task")

    # Return task...
```

**Checklist**:
- [ ] Added authentication
- [ ] Added ownership verification
- [ ] Tested can access own tasks
- [ ] Tested cannot access other users' tasks

##### Task 1.5b: GET /tasks/{task_id}/clips
**Line**: 674

**Same changes**: Add auth + ownership check

**Checklist**:
- [ ] Added authentication
- [ ] Added ownership verification
- [ ] Tested clip access control works

---

#### Task 1.6: Update Task Router Endpoints
**File**: `/home/user/supoclip/backend/src/api/routes/tasks.py`
**Status**: ⬜ Not Started

**Endpoints to update**:

1. **GET /tasks/{task_id}** (line 116)
   ```python
   async def get_task(
       task_id: str,
       current_user: str = Depends(get_current_user),  # ✅ Add
       db: AsyncSession = Depends(get_db)
   ):
       task = await task_service.get_task_with_clips(task_id)

       # ✅ Add ownership check
       if task["user_id"] != current_user:
           raise HTTPException(403, "Not authorized")

       return task
   ```

2. **GET /tasks/{task_id}/clips** (line 135) - same changes

3. **PATCH /tasks/{task_id}** (line 226)
   ```python
   async def update_task(
       task_id: str,
       request: Request,
       current_user: str = Depends(get_current_user),  # ✅ Add
       db: AsyncSession = Depends(get_db)
   ):
       # Get task and verify ownership
       task = await task_service.task_repo.get_task_by_id(db, task_id)

       # ✅ Add ownership check
       if task["user_id"] != current_user:
           raise HTTPException(403, "Not authorized")

       # Continue with update...
   ```

**Checklist**:
- [ ] GET /tasks/{task_id} secured
- [ ] GET /tasks/{task_id}/clips secured
- [ ] GET /tasks/{task_id}/progress secured
- [ ] PATCH /tasks/{task_id} secured
- [ ] All endpoints verify ownership

---

### Phase 2: Additional Security (High Priority)

#### Task 2.1: Fix Stripe Webhook
**File**: `/home/user/supoclip/backend/src/api/routes/billing.py`
**Line**: 320
**Status**: ⬜ Not Started

**Uncomment and configure webhook verification**:
```python
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        # ✅ UNCOMMENT THIS SECTION
        import stripe
        stripe.api_key = STRIPE_API_KEY

        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )

        # Handle events...
        if event["type"] == "checkout.session.completed":
            # Process payment...
```

**Checklist**:
- [ ] Uncommented webhook verification code
- [ ] Set STRIPE_WEBHOOK_SECRET in environment
- [ ] Tested webhook signature validation
- [ ] Tested invalid signatures are rejected

---

#### Task 2.2: Secure Static File Serving
**File**: `/home/user/supoclip/backend/src/main.py`
**Lines**: 140-147
**Status**: ⬜ Not Started

**Current** (publicly accessible):
```python
app.mount("/clips", StaticFiles(directory=str(clips_dir)), name="clips")
```

**Option A: Add authentication endpoint**:
```python
# Remove static mount, add authenticated endpoint
@app.get("/clips/{task_id}/{filename}")
async def serve_clip(
    task_id: str,
    filename: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify user owns the task
    task = await get_task(task_id, db)
    if task.user_id != current_user:
        raise HTTPException(403, "Not authorized")

    # Serve file
    clip_path = clips_dir / filename
    if not clip_path.exists():
        raise HTTPException(404, "Clip not found")

    return FileResponse(clip_path)
```

**Option B: Use CDN with signed URLs** (recommended for production)

**Checklist**:
- [ ] Static mounts removed or secured
- [ ] Authenticated clip serving implemented
- [ ] OR CDN with signed URLs configured
- [ ] Tested unauthorized access is blocked

---

### Phase 3: Testing (Required)

#### Task 3.1: Security Tests
**Status**: ⬜ Not Started

Create `/home/user/supoclip/backend/tests/test_security.py`:

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_endpoints_require_auth():
    """Test authentication is required"""
    endpoints = [
        "/tasks/test-id",
        "/tasks/test-id/clips",
        "/upload",
        "/start",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401

def test_cors_restrictions():
    """Test CORS only allows whitelisted origins"""
    response = client.get(
        "/",
        headers={"Origin": "https://evil.com"}
    )
    assert "Access-Control-Allow-Origin" not in response.headers

def test_rate_limiting():
    """Test rate limiting works"""
    # Make 11 requests (limit is 10)
    for i in range(11):
        response = client.post(
            "/start",
            json={"source": {"url": "test"}},
            headers={"user_id": "test-user"}
        )

    assert response.status_code == 429

def test_file_upload_validation():
    """Test file upload rejects invalid files"""
    response = client.post(
        "/upload",
        files={"video": ("test.exe", b"fake content", "application/x-executable")},
        headers={"user_id": "test-user"}
    )
    assert response.status_code == 400
```

**Checklist**:
- [ ] Created test file
- [ ] All tests pass
- [ ] Added tests to CI/CD

---

#### Task 3.2: Manual Testing
**Status**: ⬜ Not Started

```bash
# Test 1: Authentication
curl http://localhost:8000/tasks/test-id
# Expected: 401 Unauthorized ✅

# Test 2: CORS
curl -H "Origin: https://evil.com" http://localhost:8000/
# Expected: No Access-Control-Allow-Origin header ✅

# Test 3: Rate limiting
for i in {1..11}; do
  curl -H "user_id: test" http://localhost:8000/start
done
# Expected: 11th request returns 429 ✅

# Test 4: File validation
curl -F "video=@test.exe" -H "user_id: test" http://localhost:8000/upload
# Expected: 400 File type not allowed ✅

# Test 5: Security headers
curl -I http://localhost:8000/
# Expected: X-Frame-Options, CSP, HSTS, etc. ✅
```

**Checklist**:
- [ ] All manual tests pass
- [ ] Documented test results
- [ ] Security team approved

---

### Phase 4: Deployment (Final)

#### Task 4.1: Environment Configuration
**Status**: ⬜ Not Started

Create production `.env`:
```bash
# CORS
ALLOWED_ORIGINS=https://supoclip.com,https://app.supoclip.com

# Redis
REDIS_HOST=production-redis.example.com
REDIS_PORT=6379

# Stripe
STRIPE_API_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Database
DATABASE_URL=postgresql://user:pass@db.example.com:5432/supoclip

# Security
MAX_FILE_SIZE_MB=500
RATE_LIMIT_ENABLED=true
```

**Checklist**:
- [ ] All secrets in environment variables
- [ ] No hardcoded secrets in code
- [ ] Production origins configured
- [ ] Redis connection tested
- [ ] Database SSL enabled

---

#### Task 4.2: Infrastructure Setup
**Status**: ⬜ Not Started

**Checklist**:
- [ ] Redis instance running
- [ ] PostgreSQL with SSL/TLS
- [ ] HTTPS enabled (nginx/CloudFlare)
- [ ] HTTPS redirect configured
- [ ] DDoS protection enabled
- [ ] WAF configured
- [ ] Monitoring enabled
- [ ] Logging configured

---

#### Task 4.3: Final Security Verification
**Status**: ⬜ Not Started

**Pre-deployment checklist**:
- [ ] All critical tasks completed
- [ ] All tests passing
- [ ] Security scan run (bandit, safety)
- [ ] Peer review completed
- [ ] Security team sign-off
- [ ] Staging deployment successful
- [ ] Staging security tests passed

**Deployment checklist**:
- [ ] Production environment configured
- [ ] Backup and rollback plan ready
- [ ] Deploy to production
- [ ] Post-deployment security tests
- [ ] Monitor for 24 hours
- [ ] Security incident plan documented

---

## 📊 Progress Tracking

### Overall Progress

- [ ] **Phase 1: Core Security** (0/6 tasks)
  - [ ] Task 1.1: Update CORS
  - [ ] Task 1.2: Secure /start
  - [ ] Task 1.3: Secure /start-with-progress
  - [ ] Task 1.4: Secure /upload
  - [ ] Task 1.5: Secure task endpoints
  - [ ] Task 1.6: Update task router

- [ ] **Phase 2: Additional Security** (0/2 tasks)
  - [ ] Task 2.1: Fix Stripe webhook
  - [ ] Task 2.2: Secure static files

- [ ] **Phase 3: Testing** (0/2 tasks)
  - [ ] Task 3.1: Security tests
  - [ ] Task 3.2: Manual testing

- [ ] **Phase 4: Deployment** (0/3 tasks)
  - [ ] Task 4.1: Environment config
  - [ ] Task 4.2: Infrastructure setup
  - [ ] Task 4.3: Final verification

**Total Progress**: 0/13 tasks (0%)

---

## 🎯 Quick Wins (Do These First)

1. **Update CORS** (5 min) - Task 1.1
2. **Install dependencies** (5 min)
3. **Secure /upload** (15 min) - Task 1.4
4. **Add auth to /start** (10 min) - Task 1.2

**Total**: 35 minutes for 4 critical fixes

---

## 📞 Need Help?

**Implementation Guide**: See `SECURITY_HARDENING_GUIDE.md`
**Detailed Report**: See `SECURITY_AUDIT_REPORT.md`
**Code Examples**: See `main_secure.py`

**Questions?** security@supoclip.com
