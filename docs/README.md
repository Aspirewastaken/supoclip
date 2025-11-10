# SupoClip API Documentation

This directory contains comprehensive API documentation for the SupoClip project.

## Documentation Files

### 📘 API.md
**Location**: `/home/user/supoclip/docs/API.md`

Complete API reference documentation including:
- Overview and features
- Authentication guide
- Rate limiting information
- Error codes reference
- All endpoints organized by feature:
  - Video Processing
  - Task Management
  - AI Titles
  - Analytics
  - Calendar Scheduling
  - Watermarks
  - Posting Helper
  - Resources
- Code examples in:
  - Python
  - JavaScript (Node.js)
  - JavaScript (Browser/Frontend)
  - cURL
- Webhooks (planned)

### 📦 Postman Collection
**Location**: `/home/user/supoclip/docs/SupoClip_API.postman_collection.json`

Import this file into Postman to:
- Test all API endpoints
- Use pre-configured requests
- Automatic variable extraction (task_id, clip_id)
- Environment variables for easy switching between dev/prod

**How to Import**:
1. Open Postman
2. Click "Import" button
3. Select the `SupoClip_API.postman_collection.json` file
4. Set environment variables:
   - `base_url`: Your API URL (default: http://localhost:8000)
   - `user_id`: Your user UUID

### 🎮 Interactive API Playground
**Location**: `/home/user/supoclip/frontend/src/app/api-playground/page.tsx`

**Access**: Navigate to `/api-playground` in the frontend application

Interactive browser-based API testing tool with:
- All endpoints organized by category
- Visual request builder
- Automatic path parameter replacement
- Query parameter builder
- JSON request body editor
- Real-time response viewer
- Authentication support
- Color-coded HTTP methods
- No additional tools required

### 📖 OpenAPI/Swagger Documentation
**Location**: Enhanced in `/home/user/supoclip/backend/src/main.py`

**Access**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Enhanced with:
- Detailed endpoint descriptions
- Request/response examples
- Error response examples
- Authentication requirements
- Contact and license information
- Multiple server configurations

## Quick Start

### 1. Using the Interactive Playground (Easiest)

```bash
cd frontend
npm run dev
```

Navigate to `http://localhost:3000/api-playground`

### 2. Using Swagger UI

Start the backend:
```bash
cd backend
uvicorn src.main:app --reload
```

Navigate to `http://localhost:8000/docs`

### 3. Using Postman

1. Import the collection: `docs/SupoClip_API.postman_collection.json`
2. Set environment variables
3. Start testing!

### 4. Using cURL

Examples from `API.md`:

```bash
# Process a YouTube video
curl -X POST "http://localhost:8000/start" \
  -H "user_id: your-user-uuid" \
  -H "Content-Type: application/json" \
  -d '{
    "source": {
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    }
  }'
```

## Documentation Features

### ✅ Complete Coverage

All endpoints documented with:
- **Method**: GET, POST, PATCH, DELETE, PUT
- **Path**: Full endpoint path with parameter placeholders
- **Description**: Clear explanation of what the endpoint does
- **Authentication**: Whether user_id header is required
- **Request Body**: Example JSON with all fields
- **Query Parameters**: All available parameters with descriptions
- **Response Examples**: Success and error response examples
- **Error Codes**: All possible HTTP status codes

### ✅ Multi-Language Examples

Code examples provided in:
- **Python**: Using `requests` library
- **JavaScript (Node.js)**: Using `axios` and `EventSource`
- **JavaScript (Browser)**: Using `fetch` API
- **cURL**: For command-line testing

### ✅ Interactive Testing

Three ways to test interactively:
1. **API Playground** (Browser-based, no setup)
2. **Swagger UI** (Auto-generated, always up-to-date)
3. **Postman** (Professional tool, advanced features)

### ✅ Real-Time Features

Documentation includes:
- **Server-Sent Events (SSE)**: Progress tracking examples
- **File Uploads**: Multipart form data examples
- **Authentication**: Header-based auth examples
- **Rate Limiting**: Documented limits and headers

## API Endpoint Categories

### 🎬 Video Processing (3 endpoints)
- POST `/start` - Synchronous video processing
- POST `/start-with-progress` - Async with SSE progress
- POST `/upload` - Upload video file

### 📋 Task Management (7 endpoints)
- GET `/tasks` - List all tasks
- POST `/tasks` - Create new task
- GET `/tasks/{task_id}` - Get task details
- GET `/tasks/{task_id}/clips` - Get task clips
- GET `/tasks/{task_id}/progress` - SSE progress updates
- PATCH `/tasks/{task_id}` - Update task
- DELETE `/tasks/{task_id}` - Delete task
- DELETE `/tasks/{task_id}/clips/{clip_id}` - Delete clip

### 💡 AI Titles (4 endpoints)
- POST `/ai/generate-titles` - Generate viral titles
- POST `/ai/generate-titles/clip/{clip_id}` - Titles for existing clip
- GET `/ai/title-styles` - Get available styles
- GET `/ai/platforms` - Get supported platforms

### 📊 Analytics (3 endpoints)
- POST `/analytics/record` - Record metrics
- GET `/analytics/clip/{clip_id}` - Get clip performance
- GET `/analytics/dashboard` - Dashboard statistics

### 📅 Calendar (7 endpoints)
- GET `/calendar/oauth/google/url` - Google OAuth URL
- POST `/calendar/oauth/google/callback` - OAuth callback
- POST `/calendar/credentials/caldav` - Add CalDAV credentials
- GET `/calendar/credentials` - List credentials
- POST `/calendar/schedule` - Schedule post
- GET `/calendar/events` - List scheduled posts
- DELETE `/calendar/events/{id}` - Delete scheduled post
- PATCH `/calendar/events/{id}` - Update scheduled post

### 🎨 Watermarks (5 endpoints)
- POST `/watermarks/upload` - Upload watermark
- GET `/watermarks` - List watermarks
- GET `/watermarks/{account_id}` - Get watermark
- PUT `/watermarks/{account_id}/metadata` - Update metadata
- DELETE `/watermarks/{account_id}` - Delete watermark

### 📱 Posting Helper (2 endpoints)
- POST `/posting/analyze-screenshot` - Analyze screenshot
- POST `/posting/generate-content` - Generate content

### 🎨 Resources (3 endpoints)
- GET `/fonts` - List available fonts
- GET `/fonts/{font_name}` - Get font file
- GET `/transitions` - List transitions

## Authentication

All endpoints (except Core and Resources) require authentication via the `user_id` header:

```
user_id: your-user-uuid
```

Get your user_id from the frontend authentication system.

## Rate Limits

| Endpoint Type | Rate Limit |
|--------------|------------|
| Video Processing | 10 requests/hour |
| AI Operations | 50 requests/hour |
| Analytics | 100 requests/minute |
| Other | 100 requests/minute |

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "OPTIONAL_ERROR_CODE",
  "timestamp": "2025-11-10T12:00:00Z"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

## Support

- **API Documentation**: `/docs/API.md`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **API Playground**: `http://localhost:3000/api-playground`
- **GitHub Issues**: https://github.com/yourusername/supoclip/issues

## Contributing

When adding new endpoints:
1. Update `/backend/src/main.py` with OpenAPI decorators
2. Add examples to `/docs/API.md`
3. Add to Postman collection
4. Add to API Playground endpoint list
5. Update this README

## License

MIT License - See LICENSE file for details.
