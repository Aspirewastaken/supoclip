"""
Security Headers Middleware
Adds security headers to all responses
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    Headers added:
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable XSS filtering (legacy browsers)
    - Strict-Transport-Security: Enforce HTTPS
    - Content-Security-Policy: Control resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Enforce HTTPS (only in production)
        # 31536000 seconds = 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy
        # This is a restrictive policy - adjust based on your needs
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Adjust for production
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' https:",
            "media-src 'self' blob:",
            "object-src 'none'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Control browser features
        permissions_policy = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()"
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_policy)

        # Remove server header to avoid information disclosure
        if "Server" in response.headers:
            del response.headers["Server"]

        return response


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Secure CORS middleware with proper origin validation.

    Instead of allowing all origins, this validates against a whitelist.
    """

    def __init__(self, app, allowed_origins: list[str] = None):
        super().__init__(app)
        # Default allowed origins for development
        self.allowed_origins = allowed_origins or [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "https://supoclip.com",
            "https://www.supoclip.com",
            "https://app.supoclip.com"
        ]
        logger.info(f"CORS allowed origins: {self.allowed_origins}")

    def is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is in whitelist"""
        if origin in self.allowed_origins:
            return True

        # Allow localhost with any port for development
        if origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:"):
            return True

        return False

    async def dispatch(self, request: Request, call_next):
        # Handle preflight requests
        if request.method == "OPTIONS":
            origin = request.headers.get("origin")

            if origin and self.is_origin_allowed(origin):
                return Response(
                    status_code=200,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization, user_id, x-user-id",
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Max-Age": "86400",  # 24 hours
                    }
                )
            else:
                # Reject preflight for disallowed origins
                return Response(status_code=403)

        # Process request
        response = await call_next(request)

        # Add CORS headers to response
        origin = request.headers.get("origin")
        if origin and self.is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = "Content-Length, Content-Type"
        else:
            # For requests without origin or disallowed origins, don't add CORS headers
            logger.warning(f"Request from disallowed origin: {origin}")

        return response
