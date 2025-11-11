"""
File Upload Validation Utilities
Provides secure file upload validation
"""
from pathlib import Path
from typing import Optional, Tuple
import magic  # python-magic for MIME type detection
import logging
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)


class FileValidator:
    """Validates uploaded files for security"""

    # Allowed video MIME types
    ALLOWED_VIDEO_MIMETYPES = {
        "video/mp4",
        "video/mpeg",
        "video/quicktime",  # .mov
        "video/x-msvideo",  # .avi
        "video/x-matroska",  # .mkv
        "video/webm",
    }

    # Allowed video extensions
    ALLOWED_VIDEO_EXTENSIONS = {
        ".mp4", ".mpeg", ".mpg", ".mov", ".avi", ".mkv", ".webm"
    }

    # Maximum file size: 500 MB
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB in bytes

    # Minimum file size: 1 KB (to prevent empty files)
    MIN_FILE_SIZE = 1024  # 1 KB

    @staticmethod
    def validate_filename(filename: str) -> bool:
        """
        Validate filename for path traversal attempts.

        Args:
            filename: The filename to validate

        Returns:
            True if filename is safe

        Raises:
            HTTPException: If filename is unsafe
        """
        if not filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        # Check for path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            logger.warning(f"Path traversal attempt detected in filename: {filename}")
            raise HTTPException(
                status_code=400,
                detail="Invalid filename: path traversal detected"
            )

        # Check for null bytes
        if "\0" in filename:
            logger.warning(f"Null byte detected in filename: {filename}")
            raise HTTPException(
                status_code=400,
                detail="Invalid filename: null byte detected"
            )

        # Check filename length
        if len(filename) > 255:
            raise HTTPException(
                status_code=400,
                detail="Filename too long (max 255 characters)"
            )

        return True

    @staticmethod
    def validate_extension(filename: str) -> bool:
        """
        Validate file extension.

        Args:
            filename: The filename to check

        Returns:
            True if extension is allowed

        Raises:
            HTTPException: If extension is not allowed
        """
        extension = Path(filename).suffix.lower()

        if extension not in FileValidator.ALLOWED_VIDEO_EXTENSIONS:
            logger.warning(f"Disallowed file extension: {extension}")
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(FileValidator.ALLOWED_VIDEO_EXTENSIONS)}"
            )

        return True

    @staticmethod
    async def validate_file_size(file: UploadFile) -> bool:
        """
        Validate file size without reading entire file into memory.

        Args:
            file: The uploaded file

        Returns:
            True if size is valid

        Raises:
            HTTPException: If file size is invalid
        """
        # Read file in chunks to determine size
        file_size = 0
        chunk_size = 1024 * 1024  # 1 MB chunks

        # Save current position
        await file.seek(0)

        try:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                file_size += len(chunk)

                # Check if file exceeds max size
                if file_size > FileValidator.MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size is {FileValidator.MAX_FILE_SIZE // (1024*1024)} MB"
                    )

            # Check minimum size
            if file_size < FileValidator.MIN_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail="File too small or empty"
                )

            logger.info(f"File size validation passed: {file_size} bytes")
            return True

        finally:
            # Reset file position for subsequent reads
            await file.seek(0)

    @staticmethod
    async def validate_mime_type(file: UploadFile) -> bool:
        """
        Validate MIME type using magic numbers (file content).
        More secure than relying on file extension alone.

        Args:
            file: The uploaded file

        Returns:
            True if MIME type is valid

        Raises:
            HTTPException: If MIME type is not allowed
        """
        # Read first 2048 bytes for magic number detection
        await file.seek(0)
        header = await file.read(2048)
        await file.seek(0)

        try:
            # Detect MIME type from file content
            mime = magic.from_buffer(header, mime=True)

            if mime not in FileValidator.ALLOWED_VIDEO_MIMETYPES:
                logger.warning(f"Disallowed MIME type detected: {mime}")
                raise HTTPException(
                    status_code=400,
                    detail=f"File type not allowed. Detected type: {mime}"
                )

            logger.info(f"MIME type validation passed: {mime}")
            return True

        except Exception as e:
            logger.error(f"Error detecting MIME type: {e}")
            # If magic detection fails, reject the file for safety
            raise HTTPException(
                status_code=400,
                detail="Unable to determine file type"
            )

    @staticmethod
    async def validate_upload(file: UploadFile) -> Tuple[bool, str]:
        """
        Complete validation of uploaded file.

        Performs all security checks:
        1. Filename validation (path traversal)
        2. Extension validation
        3. File size validation
        4. MIME type validation (magic numbers)

        Args:
            file: The uploaded file

        Returns:
            Tuple of (is_valid, sanitized_filename)

        Raises:
            HTTPException: If any validation fails
        """
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        logger.info(f"Validating upload: {file.filename}")

        # 1. Validate filename
        FileValidator.validate_filename(file.filename)

        # 2. Validate extension
        FileValidator.validate_extension(file.filename)

        # 3. Validate file size
        await FileValidator.validate_file_size(file)

        # 4. Validate MIME type (content-based)
        await FileValidator.validate_mime_type(file)

        # All validations passed
        logger.info(f"All validations passed for: {file.filename}")

        # Return sanitized filename (just the basename)
        sanitized_filename = Path(file.filename).name

        return True, sanitized_filename


# Convenience function for FastAPI dependencies
async def validate_video_upload(file: UploadFile) -> UploadFile:
    """
    FastAPI dependency for video upload validation.

    Usage:
        @app.post("/upload")
        async def upload_video(file: UploadFile = Depends(validate_video_upload)):
            # file is already validated
            ...

    Args:
        file: Uploaded file

    Returns:
        The validated file

    Raises:
        HTTPException: If validation fails
    """
    await FileValidator.validate_upload(file)
    return file
