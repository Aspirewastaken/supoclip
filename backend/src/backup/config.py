"""
Backup Configuration Module

Handles all configuration settings for the backup system.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Literal
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BackupConfig:
    """Configuration for backup and recovery operations"""

    # Database Configuration
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://supoclip:supoclip_password@localhost:5432/supoclip"
        )
    )

    # Directories
    temp_dir: Path = field(
        default_factory=lambda: Path(os.getenv("TEMP_DIR", "/tmp"))
    )
    backup_dir: Path = field(
        default_factory=lambda: Path(os.getenv("BACKUP_DIR", "/tmp/backups"))
    )
    uploads_dir: Path = field(
        default_factory=lambda: Path(os.getenv("TEMP_DIR", "/tmp")) / "uploads"
    )
    clips_dir: Path = field(
        default_factory=lambda: Path(os.getenv("TEMP_DIR", "/tmp")) / "clips"
    )

    # Storage Backend
    storage_backend: Literal["local", "s3", "b2"] = field(
        default_factory=lambda: os.getenv("BACKUP_STORAGE_BACKEND", "local")
    )

    # S3/B2 Configuration
    s3_bucket: Optional[str] = field(
        default_factory=lambda: os.getenv("BACKUP_S3_BUCKET")
    )
    s3_region: str = field(
        default_factory=lambda: os.getenv("BACKUP_S3_REGION", "us-east-1")
    )
    s3_endpoint: Optional[str] = field(
        default_factory=lambda: os.getenv("BACKUP_S3_ENDPOINT")  # For B2 or custom S3
    )
    s3_access_key: Optional[str] = field(
        default_factory=lambda: os.getenv("BACKUP_S3_ACCESS_KEY")
    )
    s3_secret_key: Optional[str] = field(
        default_factory=lambda: os.getenv("BACKUP_S3_SECRET_KEY")
    )

    # Backup Settings
    retention_days: int = field(
        default_factory=lambda: int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    )
    compression: bool = field(
        default_factory=lambda: os.getenv("BACKUP_COMPRESSION", "true").lower() == "true"
    )
    encryption: bool = field(
        default_factory=lambda: os.getenv("BACKUP_ENCRYPTION", "false").lower() == "true"
    )
    encryption_key: Optional[str] = field(
        default_factory=lambda: os.getenv("BACKUP_ENCRYPTION_KEY")
    )

    # Incremental Backup Settings
    enable_incremental: bool = field(
        default_factory=lambda: os.getenv("BACKUP_INCREMENTAL", "true").lower() == "true"
    )
    full_backup_interval_days: int = field(
        default_factory=lambda: int(os.getenv("BACKUP_FULL_INTERVAL_DAYS", "7"))
    )

    # Backup Schedule
    daily_backup_time: str = field(
        default_factory=lambda: os.getenv("BACKUP_DAILY_TIME", "02:00")
    )
    weekly_backup_day: int = field(
        default_factory=lambda: int(os.getenv("BACKUP_WEEKLY_DAY", "0"))  # 0 = Monday
    )

    # Verification
    verify_after_backup: bool = field(
        default_factory=lambda: os.getenv("BACKUP_VERIFY", "true").lower() == "true"
    )

    # Notifications
    notification_email: Optional[str] = field(
        default_factory=lambda: os.getenv("BACKUP_NOTIFICATION_EMAIL")
    )
    notification_webhook: Optional[str] = field(
        default_factory=lambda: os.getenv("BACKUP_NOTIFICATION_WEBHOOK")
    )

    # PostgreSQL specific
    pg_host: Optional[str] = None
    pg_port: Optional[int] = None
    pg_database: Optional[str] = None
    pg_user: Optional[str] = None
    pg_password: Optional[str] = None

    def __post_init__(self):
        """Parse database URL and create directories"""
        self._parse_database_url()
        self._create_directories()

    def _parse_database_url(self):
        """Extract PostgreSQL connection details from DATABASE_URL"""
        from urllib.parse import urlparse

        # Handle asyncpg URL format
        url = self.database_url.replace("postgresql+asyncpg://", "postgresql://")
        parsed = urlparse(url)

        self.pg_host = parsed.hostname or "localhost"
        self.pg_port = parsed.port or 5432
        self.pg_database = parsed.path.lstrip("/") or "supoclip"
        self.pg_user = parsed.username or "supoclip"
        self.pg_password = parsed.password or ""

    def _create_directories(self):
        """Ensure all backup directories exist"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        (self.backup_dir / "database").mkdir(exist_ok=True)
        (self.backup_dir / "files").mkdir(exist_ok=True)
        (self.backup_dir / "metadata").mkdir(exist_ok=True)
        (self.backup_dir / "logs").mkdir(exist_ok=True)

    def get_pg_connection_string(self) -> str:
        """Get PostgreSQL connection string for pg_dump"""
        return f"postgresql://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_database}"

    def get_pg_env(self) -> dict:
        """Get environment variables for PostgreSQL commands"""
        return {
            "PGHOST": self.pg_host,
            "PGPORT": str(self.pg_port),
            "PGDATABASE": self.pg_database,
            "PGUSER": self.pg_user,
            "PGPASSWORD": self.pg_password,
        }
