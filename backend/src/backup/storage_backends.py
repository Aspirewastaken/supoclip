"""
Storage Backend Implementations

Provides abstraction layer for different storage backends:
- Local filesystem
- AWS S3
- Backblaze B2
- S3-compatible storage
"""

import asyncio
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends"""

    @abstractmethod
    async def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Upload a file to the storage backend"""
        pass

    @abstractmethod
    async def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Download a file from the storage backend"""
        pass

    @abstractmethod
    async def list_files(self, prefix: str = "") -> List[str]:
        """List files in the storage backend"""
        pass

    @abstractmethod
    async def delete_file(self, remote_path: str) -> bool:
        """Delete a file from the storage backend"""
        pass

    @abstractmethod
    async def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists in the storage backend"""
        pass

    @abstractmethod
    async def get_file_size(self, remote_path: str) -> Optional[int]:
        """Get the size of a file in bytes"""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend"""

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, remote_path: str) -> Path:
        """Get full local path from remote path"""
        return self.base_path / remote_path.lstrip("/")

    async def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Copy file to local backup directory"""
        try:
            dest_path = self._get_full_path(remote_path)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Use async copy in thread pool
            await asyncio.to_thread(shutil.copy2, local_path, dest_path)

            logger.info(f"Uploaded {local_path} to {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            return False

    async def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Copy file from local backup directory"""
        try:
            src_path = self._get_full_path(remote_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)

            await asyncio.to_thread(shutil.copy2, src_path, local_path)

            logger.info(f"Downloaded {src_path} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download {remote_path}: {e}")
            return False

    async def list_files(self, prefix: str = "") -> List[str]:
        """List files in local backup directory"""
        try:
            base_path = self._get_full_path(prefix)
            if not base_path.exists():
                return []

            files = []
            for path in base_path.rglob("*"):
                if path.is_file():
                    rel_path = path.relative_to(self.base_path)
                    files.append(str(rel_path))

            return sorted(files)
        except Exception as e:
            logger.error(f"Failed to list files with prefix {prefix}: {e}")
            return []

    async def delete_file(self, remote_path: str) -> bool:
        """Delete file from local backup directory"""
        try:
            file_path = self._get_full_path(remote_path)
            if file_path.exists():
                await asyncio.to_thread(file_path.unlink)
                logger.info(f"Deleted {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {remote_path}: {e}")
            return False

    async def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in local backup directory"""
        return self._get_full_path(remote_path).exists()

    async def get_file_size(self, remote_path: str) -> Optional[int]:
        """Get file size in bytes"""
        try:
            path = self._get_full_path(remote_path)
            if path.exists():
                return path.stat().st_size
        except Exception as e:
            logger.error(f"Failed to get size of {remote_path}: {e}")
        return None


class S3StorageBackend(StorageBackend):
    """AWS S3 storage backend"""

    def __init__(self, bucket: str, region: str, access_key: str, secret_key: str, endpoint: Optional[str] = None):
        self.bucket = bucket
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint = endpoint

        try:
            import boto3
            from botocore.config import Config

            config = Config(
                region_name=region,
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'adaptive'}
            )

            if endpoint:
                self.s3_client = boto3.client(
                    's3',
                    endpoint_url=endpoint,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    config=config
                )
            else:
                self.s3_client = boto3.client(
                    's3',
                    region_name=region,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    config=config
                )

            logger.info(f"Initialized S3 backend for bucket: {bucket}")
        except ImportError:
            raise ImportError("boto3 is required for S3 backend. Install with: pip install boto3")

    async def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Upload file to S3"""
        try:
            remote_path = remote_path.lstrip("/")

            await asyncio.to_thread(
                self.s3_client.upload_file,
                str(local_path),
                self.bucket,
                remote_path,
                ExtraArgs={'ServerSideEncryption': 'AES256'}
            )

            logger.info(f"Uploaded {local_path} to s3://{self.bucket}/{remote_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {local_path} to S3: {e}")
            return False

    async def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Download file from S3"""
        try:
            remote_path = remote_path.lstrip("/")
            local_path.parent.mkdir(parents=True, exist_ok=True)

            await asyncio.to_thread(
                self.s3_client.download_file,
                self.bucket,
                remote_path,
                str(local_path)
            )

            logger.info(f"Downloaded s3://{self.bucket}/{remote_path} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download {remote_path} from S3: {e}")
            return False

    async def list_files(self, prefix: str = "") -> List[str]:
        """List files in S3 bucket"""
        try:
            prefix = prefix.lstrip("/")
            paginator = self.s3_client.get_paginator('list_objects_v2')

            files = []
            async for page in asyncio.to_thread(
                lambda: paginator.paginate(Bucket=self.bucket, Prefix=prefix)
            ):
                for obj in page.get('Contents', []):
                    files.append(obj['Key'])

            return sorted(files)
        except Exception as e:
            logger.error(f"Failed to list S3 files with prefix {prefix}: {e}")
            return []

    async def delete_file(self, remote_path: str) -> bool:
        """Delete file from S3"""
        try:
            remote_path = remote_path.lstrip("/")

            await asyncio.to_thread(
                self.s3_client.delete_object,
                Bucket=self.bucket,
                Key=remote_path
            )

            logger.info(f"Deleted s3://{self.bucket}/{remote_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {remote_path} from S3: {e}")
            return False

    async def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in S3"""
        try:
            remote_path = remote_path.lstrip("/")

            await asyncio.to_thread(
                self.s3_client.head_object,
                Bucket=self.bucket,
                Key=remote_path
            )
            return True
        except:
            return False

    async def get_file_size(self, remote_path: str) -> Optional[int]:
        """Get file size from S3"""
        try:
            remote_path = remote_path.lstrip("/")

            response = await asyncio.to_thread(
                self.s3_client.head_object,
                Bucket=self.bucket,
                Key=remote_path
            )
            return response.get('ContentLength')
        except Exception as e:
            logger.error(f"Failed to get size of {remote_path}: {e}")
            return None


class B2StorageBackend(S3StorageBackend):
    """
    Backblaze B2 storage backend

    B2 is S3-compatible, so we inherit from S3StorageBackend
    with B2-specific endpoint configuration.
    """

    def __init__(self, bucket: str, key_id: str, application_key: str):
        # B2 endpoint format: https://s3.{region}.backblazeb2.com
        # The region is extracted from the bucket name or set to default
        endpoint = "https://s3.us-west-004.backblazeb2.com"  # Default endpoint

        super().__init__(
            bucket=bucket,
            region="us-west-004",
            access_key=key_id,
            secret_key=application_key,
            endpoint=endpoint
        )

        logger.info(f"Initialized B2 backend for bucket: {bucket}")


def get_storage_backend(config) -> StorageBackend:
    """Factory function to create appropriate storage backend"""
    if config.storage_backend == "local":
        return LocalStorageBackend(config.backup_dir)

    elif config.storage_backend == "s3":
        if not all([config.s3_bucket, config.s3_access_key, config.s3_secret_key]):
            raise ValueError("S3 backend requires: s3_bucket, s3_access_key, s3_secret_key")

        return S3StorageBackend(
            bucket=config.s3_bucket,
            region=config.s3_region,
            access_key=config.s3_access_key,
            secret_key=config.s3_secret_key,
            endpoint=config.s3_endpoint
        )

    elif config.storage_backend == "b2":
        if not all([config.s3_bucket, config.s3_access_key, config.s3_secret_key]):
            raise ValueError("B2 backend requires: s3_bucket (B2 bucket name), s3_access_key (key ID), s3_secret_key (application key)")

        return B2StorageBackend(
            bucket=config.s3_bucket,
            key_id=config.s3_access_key,
            application_key=config.s3_secret_key
        )

    else:
        raise ValueError(f"Unknown storage backend: {config.storage_backend}")
