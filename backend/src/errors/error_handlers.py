"""
FastAPI exception handlers for structured error responses.
"""

import logging
from typing import Union, Any, Dict
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

from .custom_exceptions import (
    BaseSupoClipException,
    ErrorCode,
    DatabaseError,
    DatabaseConnectionError,
    DuplicateRecordError,
)

logger = logging.getLogger(__name__)


async def base_exception_handler(
    request: Request,
    exc: BaseSupoClipException
) -> JSONResponse:
    """
    Handle all custom SupoClip exceptions.

    Returns structured error response with error code, message, and details.
    """
    logger.error(
        f"SupoClip Error [{exc.error_code.value}]: {exc.message}",
        extra={
            "error_code": exc.error_code.value,
            "error_type": exc.__class__.__name__,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=exc.cause if exc.cause else exc
    )

    headers = {}
    if exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)

    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict(),
        headers=headers
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Converts validation errors to structured format.
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(
        f"Validation error on {request.url.path}",
        extra={
            "errors": errors,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": ErrorCode.VALIDATION_ERROR.value,
                "message": "Validation error",
                "type": "ValidationError",
                "details": {
                    "validation_errors": errors
                }
            }
        }
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle standard HTTP exceptions.

    Converts HTTPException to structured format.
    """
    # Map HTTP status codes to error codes
    error_code_map = {
        400: ErrorCode.BAD_REQUEST,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        500: ErrorCode.INTERNAL_SERVER_ERROR,
    }

    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)

    logger.warning(
        f"HTTP Error {exc.status_code}: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code.value,
                "message": str(exc.detail),
                "type": "HTTPException"
            }
        },
        headers=getattr(exc, "headers", None)
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.

    Converts database errors to structured format with appropriate error codes.
    """
    # Determine specific error type
    if isinstance(exc, IntegrityError):
        error = DuplicateRecordError(
            message="Database integrity constraint violated",
            details={"original_error": str(exc.orig) if hasattr(exc, 'orig') else str(exc)}
        )
    elif isinstance(exc, OperationalError):
        error = DatabaseConnectionError(
            message="Database operation failed",
            details={"original_error": str(exc.orig) if hasattr(exc, 'orig') else str(exc)}
        )
    else:
        error = DatabaseError(
            message="Database error occurred",
            details={"original_error": str(exc)}
        )

    logger.error(
        f"Database Error: {exc}",
        extra={
            "error_type": exc.__class__.__name__,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=exc
    )

    return JSONResponse(
        status_code=error.http_status,
        content=error.to_dict()
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Catches all unhandled exceptions and returns generic error response.
    """
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "error_type": exc.__class__.__name__,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=exc
    )

    # Don't expose internal error details in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                "message": "An unexpected error occurred",
                "type": "InternalServerError"
            }
        }
    )


def register_error_handlers(app) -> None:
    """
    Register all error handlers with FastAPI app.

    Usage:
        from .errors.error_handlers import register_error_handlers
        register_error_handlers(app)
    """
    # Custom SupoClip exceptions
    app.add_exception_handler(BaseSupoClipException, base_exception_handler)

    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Database errors
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)

    # Catch-all for unexpected errors
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Error handlers registered successfully")


# Helper function to create error responses
def create_error_response(
    error_code: ErrorCode,
    message: str,
    status_code: int = 500,
    details: Dict[str, Any] = None
) -> JSONResponse:
    """
    Helper function to create standardized error responses.

    Usage:
        return create_error_response(
            ErrorCode.VIDEO_NOT_FOUND,
            "Video file could not be found",
            status_code=404,
            details={"video_id": "abc123"}
        )
    """
    content = {
        "error": {
            "code": error_code.value,
            "message": message,
        }
    }

    if details:
        content["error"]["details"] = details

    return JSONResponse(
        status_code=status_code,
        content=content
    )
