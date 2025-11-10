"""
CDN integration for SupoClip clip delivery.

Supports multiple CDN providers:
- AWS CloudFront (with S3 backend)
- Cloudflare R2
- Bunny CDN

Features:
- Automatic upload after clip generation
- Signed URLs for private clips
- Cache purging/invalidation
- Fallback to direct serving
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hashlib
import hmac
import base64
from urllib.parse import quote, urlencode
import asyncio

logger = logging.getLogger(__name__)


class CDNProvider(ABC):
    """Abstract base class for CDN providers"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize CDN provider with configuration.

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self.enabled = config.get('enabled', False)
        self.base_url = config.get('base_url', '')

    @abstractmethod
    async def upload(self, local_path: str, remote_path: str, content_type: str = 'video/mp4') -> bool:
        """
        Upload a file to the CDN.

        Args:
            local_path: Path to the local file
            remote_path: Destination path on CDN
            content_type: MIME type of the file

        Returns:
            True if upload successful, False otherwise
        """
        pass

    @abstractmethod
    def get_url(self, remote_path: str, signed: bool = False, expiry: int = 3600) -> str:
        """
        Get the CDN URL for a file.

        Args:
            remote_path: Path to the file on CDN
            signed: Whether to generate a signed URL for private access
            expiry: URL expiration time in seconds (for signed URLs)

        Returns:
            CDN URL for the file
        """
        pass

    @abstractmethod
    async def delete(self, remote_path: str) -> bool:
        """
        Delete a file from the CDN.

        Args:
            remote_path: Path to the file on CDN

        Returns:
            True if deletion successful, False otherwise
        """
        pass

    @abstractmethod
    async def purge(self, paths: List[str]) -> bool:
        """
        Purge/invalidate CDN cache for specific paths.

        Args:
            paths: List of paths to purge from cache

        Returns:
            True if purge successful, False otherwise
        """
        pass

    def is_enabled(self) -> bool:
        """Check if CDN is enabled"""
        return self.enabled


class CloudFrontProvider(CDNProvider):
    """AWS CloudFront CDN provider with S3 backend"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bucket_name = config.get('s3_bucket')
        self.region = config.get('aws_region', 'us-east-1')
        self.distribution_id = config.get('distribution_id')
        self.access_key = config.get('aws_access_key_id')
        self.secret_key = config.get('aws_secret_access_key')
        self.cloudfront_key_id = config.get('cloudfront_key_id')
        self.cloudfront_private_key = config.get('cloudfront_private_key_path')

        # Initialize boto3 clients if credentials are available
        self.s3_client = None
        self.cloudfront_client = None

        if self.enabled and self.access_key and self.secret_key:
            try:
                import boto3
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
                self.cloudfront_client = boto3.client(
                    'cloudfront',
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
                logger.info(f"✅ CloudFront CDN initialized with bucket: {self.bucket_name}")
            except ImportError:
                logger.error("❌ boto3 not installed. Install with: pip install boto3")
                self.enabled = False
            except Exception as e:
                logger.error(f"❌ Failed to initialize AWS clients: {e}")
                self.enabled = False

    async def upload(self, local_path: str, remote_path: str, content_type: str = 'video/mp4') -> bool:
        """Upload file to S3"""
        if not self.enabled or not self.s3_client:
            logger.warning("CloudFront CDN is not enabled or configured")
            return False

        try:
            # Remove leading slash if present
            remote_path = remote_path.lstrip('/')

            # Upload to S3 in a thread pool (boto3 is synchronous)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.upload_file(
                    local_path,
                    self.bucket_name,
                    remote_path,
                    ExtraArgs={
                        'ContentType': content_type,
                        'CacheControl': 'public, max-age=31536000',  # 1 year
                        'ACL': 'private'  # Keep files private, use signed URLs
                    }
                )
            )

            logger.info(f"✅ Uploaded to S3: s3://{self.bucket_name}/{remote_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to upload to S3: {e}")
            return False

    def get_url(self, remote_path: str, signed: bool = False, expiry: int = 3600) -> str:
        """Get CloudFront URL (optionally signed)"""
        remote_path = remote_path.lstrip('/')
        url = f"{self.base_url}/{remote_path}"

        if not signed or not self.cloudfront_key_id or not self.cloudfront_private_key:
            return url

        try:
            # Generate CloudFront signed URL
            from botocore.signers import CloudFrontSigner
            import rsa

            def rsa_signer(message):
                with open(self.cloudfront_private_key, 'rb') as key_file:
                    private_key = rsa.PrivateKey.load_pkcs1(key_file.read())
                return rsa.sign(message, private_key, 'SHA-1')

            cloudfront_signer = CloudFrontSigner(self.cloudfront_key_id, rsa_signer)

            # Set expiration time
            expire_date = datetime.utcnow() + timedelta(seconds=expiry)

            signed_url = cloudfront_signer.generate_presigned_url(
                url,
                date_less_than=expire_date
            )

            return signed_url

        except Exception as e:
            logger.error(f"❌ Failed to generate signed CloudFront URL: {e}")
            return url

    async def delete(self, remote_path: str) -> bool:
        """Delete file from S3"""
        if not self.enabled or not self.s3_client:
            return False

        try:
            remote_path = remote_path.lstrip('/')
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=remote_path
                )
            )
            logger.info(f"✅ Deleted from S3: {remote_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete from S3: {e}")
            return False

    async def purge(self, paths: List[str]) -> bool:
        """Create CloudFront invalidation"""
        if not self.enabled or not self.cloudfront_client or not self.distribution_id:
            return False

        try:
            # Ensure paths start with /
            formatted_paths = [f"/{path.lstrip('/')}" for path in paths]

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.cloudfront_client.create_invalidation(
                    DistributionId=self.distribution_id,
                    InvalidationBatch={
                        'Paths': {
                            'Quantity': len(formatted_paths),
                            'Items': formatted_paths
                        },
                        'CallerReference': str(datetime.utcnow().timestamp())
                    }
                )
            )

            logger.info(f"✅ CloudFront invalidation created: {response['Invalidation']['Id']}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create CloudFront invalidation: {e}")
            return False


class CloudflareR2Provider(CDNProvider):
    """Cloudflare R2 CDN provider"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.account_id = config.get('account_id')
        self.access_key_id = config.get('access_key_id')
        self.secret_access_key = config.get('secret_access_key')
        self.bucket_name = config.get('bucket_name')
        self.public_url = config.get('public_url')  # Custom domain or r2.dev URL

        # R2 is S3-compatible, use boto3
        self.s3_client = None

        if self.enabled and self.account_id and self.access_key_id and self.secret_access_key:
            try:
                import boto3
                # R2 endpoint format: https://<account_id>.r2.cloudflarestorage.com
                endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"

                self.s3_client = boto3.client(
                    's3',
                    endpoint_url=endpoint_url,
                    aws_access_key_id=self.access_key_id,
                    aws_secret_access_key=self.secret_access_key,
                    region_name='auto'  # R2 uses 'auto'
                )
                logger.info(f"✅ Cloudflare R2 initialized with bucket: {self.bucket_name}")
            except ImportError:
                logger.error("❌ boto3 not installed. Install with: pip install boto3")
                self.enabled = False
            except Exception as e:
                logger.error(f"❌ Failed to initialize R2 client: {e}")
                self.enabled = False

    async def upload(self, local_path: str, remote_path: str, content_type: str = 'video/mp4') -> bool:
        """Upload file to R2"""
        if not self.enabled or not self.s3_client:
            logger.warning("Cloudflare R2 is not enabled or configured")
            return False

        try:
            remote_path = remote_path.lstrip('/')

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.upload_file(
                    local_path,
                    self.bucket_name,
                    remote_path,
                    ExtraArgs={
                        'ContentType': content_type,
                        'CacheControl': 'public, max-age=31536000'
                    }
                )
            )

            logger.info(f"✅ Uploaded to R2: {self.bucket_name}/{remote_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to upload to R2: {e}")
            return False

    def get_url(self, remote_path: str, signed: bool = False, expiry: int = 3600) -> str:
        """Get R2 URL (optionally signed)"""
        remote_path = remote_path.lstrip('/')

        # Use public URL if configured (custom domain or r2.dev)
        if self.public_url:
            url = f"{self.public_url}/{remote_path}"
        else:
            url = f"{self.base_url}/{remote_path}"

        if not signed or not self.s3_client:
            return url

        try:
            # Generate presigned URL
            loop = asyncio.new_event_loop()
            presigned_url = loop.run_until_complete(
                loop.run_in_executor(
                    None,
                    lambda: self.s3_client.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': self.bucket_name,
                            'Key': remote_path
                        },
                        ExpiresIn=expiry
                    )
                )
            )
            return presigned_url

        except Exception as e:
            logger.error(f"❌ Failed to generate signed R2 URL: {e}")
            return url

    async def delete(self, remote_path: str) -> bool:
        """Delete file from R2"""
        if not self.enabled or not self.s3_client:
            return False

        try:
            remote_path = remote_path.lstrip('/')
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=remote_path
                )
            )
            logger.info(f"✅ Deleted from R2: {remote_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete from R2: {e}")
            return False

    async def purge(self, paths: List[str]) -> bool:
        """
        Purge R2 cache (via Cloudflare API if zone is configured).
        R2 doesn't have built-in cache purging, but if you're using
        Cloudflare CDN in front of R2, you can purge via Cloudflare API.
        """
        zone_id = self.config.get('cloudflare_zone_id')
        api_token = self.config.get('cloudflare_api_token')

        if not zone_id or not api_token:
            logger.warning("Cloudflare Zone ID or API token not configured for cache purging")
            return False

        try:
            import aiohttp

            # Construct full URLs for purging
            urls = [self.get_url(path) for path in paths]

            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {api_token}',
                    'Content-Type': 'application/json'
                }
                data = {'files': urls}

                async with session.post(
                    f'https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache',
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ Purged {len(urls)} files from Cloudflare cache")
                        return True
                    else:
                        logger.error(f"❌ Failed to purge cache: {await response.text()}")
                        return False

        except ImportError:
            logger.error("❌ aiohttp not installed. Install with: pip install aiohttp")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to purge Cloudflare cache: {e}")
            return False


class BunnyCDNProvider(CDNProvider):
    """Bunny CDN provider"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.storage_zone_name = config.get('storage_zone_name')
        self.storage_api_key = config.get('storage_api_key')
        self.cdn_api_key = config.get('cdn_api_key')
        self.storage_region = config.get('storage_region', 'de')  # de, ny, la, sg, etc.
        self.pull_zone_id = config.get('pull_zone_id')  # For cache purging

        # Determine storage endpoint based on region
        if self.storage_region == 'de':
            self.storage_endpoint = 'storage.bunnycdn.com'
        else:
            self.storage_endpoint = f'{self.storage_region}.storage.bunnycdn.com'

        if self.enabled and self.storage_zone_name and self.storage_api_key:
            logger.info(f"✅ Bunny CDN initialized with storage zone: {self.storage_zone_name}")
        else:
            if self.enabled:
                logger.error("❌ Bunny CDN enabled but missing required configuration")
                self.enabled = False

    async def upload(self, local_path: str, remote_path: str, content_type: str = 'video/mp4') -> bool:
        """Upload file to Bunny Storage"""
        if not self.enabled:
            logger.warning("Bunny CDN is not enabled or configured")
            return False

        try:
            import aiohttp

            remote_path = remote_path.lstrip('/')

            # Read file content
            with open(local_path, 'rb') as f:
                file_content = f.read()

            # Bunny Storage API endpoint
            url = f"https://{self.storage_endpoint}/{self.storage_zone_name}/{remote_path}"

            headers = {
                'AccessKey': self.storage_api_key,
                'Content-Type': content_type
            }

            async with aiohttp.ClientSession() as session:
                async with session.put(url, headers=headers, data=file_content) as response:
                    if response.status in [200, 201]:
                        logger.info(f"✅ Uploaded to Bunny Storage: {remote_path}")
                        return True
                    else:
                        logger.error(f"❌ Failed to upload to Bunny Storage: {response.status} - {await response.text()}")
                        return False

        except ImportError:
            logger.error("❌ aiohttp not installed. Install with: pip install aiohttp")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to upload to Bunny Storage: {e}")
            return False

    def get_url(self, remote_path: str, signed: bool = False, expiry: int = 3600) -> str:
        """Get Bunny CDN URL (optionally signed with token authentication)"""
        remote_path = remote_path.lstrip('/')
        url = f"{self.base_url}/{remote_path}"

        if not signed or not self.cdn_api_key:
            return url

        try:
            # Generate Bunny signed URL (token authentication)
            # Format: https://cdn.example.com/path?token=<signature>&expires=<timestamp>

            expires = int((datetime.utcnow() + timedelta(seconds=expiry)).timestamp())

            # Bunny token format: base64(sha256(api_key + path + expires))
            sign_string = f"{self.cdn_api_key}{remote_path}{expires}"
            signature = base64.b64encode(
                hashlib.sha256(sign_string.encode()).digest()
            ).decode().replace('+', '-').replace('/', '_').rstrip('=')

            signed_url = f"{url}?token={signature}&expires={expires}"
            return signed_url

        except Exception as e:
            logger.error(f"❌ Failed to generate signed Bunny URL: {e}")
            return url

    async def delete(self, remote_path: str) -> bool:
        """Delete file from Bunny Storage"""
        if not self.enabled:
            return False

        try:
            import aiohttp

            remote_path = remote_path.lstrip('/')
            url = f"https://{self.storage_endpoint}/{self.storage_zone_name}/{remote_path}"

            headers = {
                'AccessKey': self.storage_api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"✅ Deleted from Bunny Storage: {remote_path}")
                        return True
                    else:
                        logger.error(f"❌ Failed to delete from Bunny Storage: {response.status}")
                        return False

        except ImportError:
            logger.error("❌ aiohttp not installed. Install with: pip install aiohttp")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete from Bunny Storage: {e}")
            return False

    async def purge(self, paths: List[str]) -> bool:
        """Purge Bunny CDN cache"""
        if not self.enabled or not self.pull_zone_id or not self.cdn_api_key:
            logger.warning("Bunny CDN pull zone ID or API key not configured for cache purging")
            return False

        try:
            import aiohttp

            # Purge each URL individually (Bunny doesn't support batch purging)
            success_count = 0

            async with aiohttp.ClientSession() as session:
                for path in paths:
                    url = self.get_url(path)

                    purge_url = f"https://api.bunny.net/pullzone/{self.pull_zone_id}/purgeCache"
                    headers = {
                        'AccessKey': self.cdn_api_key,
                        'Content-Type': 'application/json'
                    }
                    data = {'url': url}

                    async with session.post(purge_url, headers=headers, json=data) as response:
                        if response.status == 200:
                            success_count += 1
                        else:
                            logger.error(f"❌ Failed to purge {url}: {response.status}")

            if success_count == len(paths):
                logger.info(f"✅ Purged {success_count} files from Bunny CDN cache")
                return True
            else:
                logger.warning(f"⚠️ Purged {success_count}/{len(paths)} files from Bunny CDN cache")
                return success_count > 0

        except ImportError:
            logger.error("❌ aiohttp not installed. Install with: pip install aiohttp")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to purge Bunny CDN cache: {e}")
            return False


# Provider registry
PROVIDERS = {
    'cloudfront': CloudFrontProvider,
    'r2': CloudflareR2Provider,
    'bunny': BunnyCDNProvider
}


def get_cdn_provider(provider_name: str = None, config: Dict[str, Any] = None) -> Optional[CDNProvider]:
    """
    Get CDN provider instance.

    Args:
        provider_name: Name of the CDN provider (cloudfront, r2, bunny)
        config: Provider configuration dictionary

    Returns:
        CDN provider instance or None if disabled/not configured
    """
    if not config:
        from ..config import Config
        app_config = Config()

        # Try to get CDN config from environment
        provider_name = provider_name or os.getenv('CDN_PROVIDER')

        if not provider_name:
            return None

        # Build config from environment variables
        config = _get_config_from_env(provider_name)

    if not provider_name or provider_name not in PROVIDERS:
        logger.warning(f"Unknown CDN provider: {provider_name}")
        return None

    provider_class = PROVIDERS[provider_name]
    provider = provider_class(config)

    if not provider.is_enabled():
        logger.info(f"CDN provider '{provider_name}' is not enabled")
        return None

    return provider


def _get_config_from_env(provider_name: str) -> Dict[str, Any]:
    """Build CDN configuration from environment variables"""

    base_config = {
        'enabled': os.getenv(f'CDN_ENABLED', 'false').lower() == 'true',
        'base_url': os.getenv('CDN_BASE_URL', '')
    }

    if provider_name == 'cloudfront':
        return {
            **base_config,
            's3_bucket': os.getenv('AWS_S3_BUCKET'),
            'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
            'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'distribution_id': os.getenv('CLOUDFRONT_DISTRIBUTION_ID'),
            'cloudfront_key_id': os.getenv('CLOUDFRONT_KEY_ID'),
            'cloudfront_private_key_path': os.getenv('CLOUDFRONT_PRIVATE_KEY_PATH')
        }

    elif provider_name == 'r2':
        return {
            **base_config,
            'account_id': os.getenv('CLOUDFLARE_ACCOUNT_ID'),
            'access_key_id': os.getenv('R2_ACCESS_KEY_ID'),
            'secret_access_key': os.getenv('R2_SECRET_ACCESS_KEY'),
            'bucket_name': os.getenv('R2_BUCKET_NAME'),
            'public_url': os.getenv('R2_PUBLIC_URL'),
            'cloudflare_zone_id': os.getenv('CLOUDFLARE_ZONE_ID'),
            'cloudflare_api_token': os.getenv('CLOUDFLARE_API_TOKEN')
        }

    elif provider_name == 'bunny':
        return {
            **base_config,
            'storage_zone_name': os.getenv('BUNNY_STORAGE_ZONE_NAME'),
            'storage_api_key': os.getenv('BUNNY_STORAGE_API_KEY'),
            'cdn_api_key': os.getenv('BUNNY_CDN_API_KEY'),
            'storage_region': os.getenv('BUNNY_STORAGE_REGION', 'de'),
            'pull_zone_id': os.getenv('BUNNY_PULL_ZONE_ID')
        }

    return base_config


# Convenience functions for common operations

async def upload_to_cdn(
    local_path: str,
    remote_path: str,
    provider: CDNProvider = None,
    content_type: str = 'video/mp4'
) -> bool:
    """
    Upload a file to CDN.

    Args:
        local_path: Path to local file
        remote_path: Destination path on CDN (e.g., 'clips/video.mp4')
        provider: CDN provider instance (auto-detected if None)
        content_type: MIME type

    Returns:
        True if successful, False otherwise
    """
    if provider is None:
        provider = get_cdn_provider()

    if provider is None:
        logger.info("No CDN provider configured, skipping upload")
        return False

    try:
        return await provider.upload(local_path, remote_path, content_type)
    except Exception as e:
        logger.error(f"❌ CDN upload failed: {e}")
        return False


def get_cdn_url(
    remote_path: str,
    provider: CDNProvider = None,
    signed: bool = False,
    expiry: int = 3600,
    fallback_url: str = None
) -> str:
    """
    Get CDN URL for a file with fallback to direct serving.

    Args:
        remote_path: Path on CDN
        provider: CDN provider instance
        signed: Whether to generate signed URL
        expiry: URL expiration in seconds
        fallback_url: Fallback URL if CDN not available

    Returns:
        CDN URL or fallback URL
    """
    if provider is None:
        provider = get_cdn_provider()

    if provider is None or not provider.is_enabled():
        return fallback_url or f"/clips/{Path(remote_path).name}"

    try:
        return provider.get_url(remote_path, signed, expiry)
    except Exception as e:
        logger.error(f"❌ Failed to get CDN URL: {e}")
        return fallback_url or f"/clips/{Path(remote_path).name}"


async def purge_cdn_cache(paths: List[str], provider: CDNProvider = None) -> bool:
    """
    Purge CDN cache for specific paths.

    Args:
        paths: List of paths to purge
        provider: CDN provider instance

    Returns:
        True if successful, False otherwise
    """
    if provider is None:
        provider = get_cdn_provider()

    if provider is None:
        logger.info("No CDN provider configured, skipping cache purge")
        return False

    try:
        return await provider.purge(paths)
    except Exception as e:
        logger.error(f"❌ CDN cache purge failed: {e}")
        return False


async def delete_from_cdn(remote_path: str, provider: CDNProvider = None) -> bool:
    """
    Delete a file from CDN.

    Args:
        remote_path: Path on CDN
        provider: CDN provider instance

    Returns:
        True if successful, False otherwise
    """
    if provider is None:
        provider = get_cdn_provider()

    if provider is None:
        logger.info("No CDN provider configured, skipping deletion")
        return False

    try:
        return await provider.delete(remote_path)
    except Exception as e:
        logger.error(f"❌ CDN deletion failed: {e}")
        return False
