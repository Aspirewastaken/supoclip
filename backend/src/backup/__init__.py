"""
Automated Backup and Recovery System for SupoClip

This module provides comprehensive backup and recovery functionality for:
- PostgreSQL database (full and incremental backups)
- Video files (original uploads and generated clips)
- Metadata and configuration

Supports multiple storage backends:
- Local filesystem
- AWS S3
- Backblaze B2
- Any S3-compatible storage
"""

from .config import BackupConfig
from .database_backup import DatabaseBackup
from .file_backup import FileBackup
from .restore import RestoreManager
from .scheduler import BackupScheduler
from .verify import BackupVerifier

__version__ = "1.0.0"

__all__ = [
    "BackupConfig",
    "DatabaseBackup",
    "FileBackup",
    "RestoreManager",
    "BackupScheduler",
    "BackupVerifier",
]
