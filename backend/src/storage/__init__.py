"""
Storage module for CDN integration and file delivery.

Supports multiple CDN providers:
- AWS CloudFront
- Cloudflare R2
- Bunny CDN
"""

from .cdn import (
    CDNProvider,
    get_cdn_provider,
    upload_to_cdn,
    get_cdn_url,
    purge_cdn_cache,
    delete_from_cdn
)

__all__ = [
    'CDNProvider',
    'get_cdn_provider',
    'upload_to_cdn',
    'get_cdn_url',
    'purge_cdn_cache',
    'delete_from_cdn'
]
