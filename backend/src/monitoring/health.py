"""
Health Check Module for SupoClip Backend

Provides comprehensive health checks for:
- Database connectivity
- Redis connectivity
- Disk space
- Memory usage
- Worker status
"""

import asyncio
import psutil
import shutil
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class HealthCheck:
    """Comprehensive health check for the SupoClip backend"""

    def __init__(self):
        self.checks: List[Dict[str, Any]] = []
        self.status = "healthy"
        self.timestamp = None

    async def check_database(self, db: AsyncSession) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = datetime.now()
            await db.execute(text("SELECT 1"))
            response_time = (datetime.now() - start_time).total_seconds() * 1000

            # Check connection pool status
            pool = db.bind.pool
            pool_size = pool.size()
            pool_checked_out = pool.checkedout()
            pool_overflow = pool.overflow()

            return {
                "name": "database",
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "details": {
                    "pool_size": pool_size,
                    "connections_in_use": pool_checked_out,
                    "overflow": pool_overflow,
                }
            }
        except Exception as e:
            self.status = "unhealthy"
            return {
                "name": "database",
                "status": "unhealthy",
                "error": str(e),
                "details": None
            }

    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            import redis.asyncio as redis
            from ..config import Config

            config = Config()
            redis_host = config.redis_host if hasattr(config, 'redis_host') else 'localhost'
            redis_port = config.redis_port if hasattr(config, 'redis_port') else 6379

            start_time = datetime.now()
            client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

            # Test connection
            await client.ping()
            response_time = (datetime.now() - start_time).total_seconds() * 1000

            # Get Redis info
            info = await client.info()
            await client.close()

            return {
                "name": "redis",
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "details": {
                    "version": info.get("redis_version", "unknown"),
                    "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                    "connected_clients": info.get("connected_clients", 0),
                }
            }
        except Exception as e:
            # Redis is optional, so we'll mark it as degraded instead of unhealthy
            if self.status == "healthy":
                self.status = "degraded"
            return {
                "name": "redis",
                "status": "degraded",
                "error": str(e),
                "details": None
            }

    def check_disk_space(self) -> Dict[str, Any]:
        """Check disk space for critical paths"""
        try:
            from ..config import Config
            config = Config()

            paths_to_check = {
                "temp_dir": config.temp_dir,
                "uploads": f"{config.temp_dir}/uploads",
                "clips": f"{config.temp_dir}/clips",
            }

            disk_info = {}
            all_healthy = True

            for name, path in paths_to_check.items():
                if Path(path).exists():
                    usage = shutil.disk_usage(path)
                    used_percent = (usage.used / usage.total) * 100
                    free_gb = usage.free / (1024 ** 3)

                    # Mark as unhealthy if less than 1GB free or >95% used
                    is_healthy = free_gb > 1.0 and used_percent < 95.0

                    disk_info[name] = {
                        "path": path,
                        "total_gb": round(usage.total / (1024 ** 3), 2),
                        "used_gb": round(usage.used / (1024 ** 3), 2),
                        "free_gb": round(free_gb, 2),
                        "used_percent": round(used_percent, 2),
                        "healthy": is_healthy
                    }

                    if not is_healthy:
                        all_healthy = False

            if not all_healthy:
                self.status = "unhealthy"

            return {
                "name": "disk_space",
                "status": "healthy" if all_healthy else "unhealthy",
                "details": disk_info
            }
        except Exception as e:
            self.status = "unhealthy"
            return {
                "name": "disk_space",
                "status": "unhealthy",
                "error": str(e),
                "details": None
            }

    def check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent

            # Mark as unhealthy if >90% memory used
            is_healthy = used_percent < 90.0

            if not is_healthy:
                if self.status == "healthy":
                    self.status = "degraded"

            return {
                "name": "memory",
                "status": "healthy" if is_healthy else "degraded",
                "details": {
                    "total_gb": round(memory.total / (1024 ** 3), 2),
                    "used_gb": round(memory.used / (1024 ** 3), 2),
                    "available_gb": round(memory.available / (1024 ** 3), 2),
                    "used_percent": round(used_percent, 2),
                }
            }
        except Exception as e:
            return {
                "name": "memory",
                "status": "unknown",
                "error": str(e),
                "details": None
            }

    def check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()

            # Mark as degraded if >80% CPU used
            is_healthy = cpu_percent < 80.0

            if not is_healthy:
                if self.status == "healthy":
                    self.status = "degraded"

            return {
                "name": "cpu",
                "status": "healthy" if is_healthy else "degraded",
                "details": {
                    "cpu_count": cpu_count,
                    "cpu_percent": round(cpu_percent, 2),
                }
            }
        except Exception as e:
            return {
                "name": "cpu",
                "status": "unknown",
                "error": str(e),
                "details": None
            }

    async def check_workers(self, db: AsyncSession) -> Dict[str, Any]:
        """Check worker status by looking at task queue"""
        try:
            # Check for pending tasks
            result = await db.execute(
                text("SELECT COUNT(*) as count FROM tasks WHERE status = 'processing'")
            )
            processing_count = result.fetchone()[0]

            # Check for old stuck tasks (processing for >1 hour)
            result = await db.execute(
                text("""
                    SELECT COUNT(*) as count
                    FROM tasks
                    WHERE status = 'processing'
                    AND updated_at < NOW() - INTERVAL '1 hour'
                """)
            )
            stuck_count = result.fetchone()[0]

            is_healthy = stuck_count == 0

            if not is_healthy:
                if self.status == "healthy":
                    self.status = "degraded"

            return {
                "name": "workers",
                "status": "healthy" if is_healthy else "degraded",
                "details": {
                    "processing_tasks": processing_count,
                    "stuck_tasks": stuck_count,
                }
            }
        except Exception as e:
            return {
                "name": "workers",
                "status": "unknown",
                "error": str(e),
                "details": None
            }

    async def run_all_checks(self, db: AsyncSession) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status"""
        self.timestamp = datetime.utcnow()
        self.status = "healthy"
        self.checks = []

        # Run all checks
        self.checks.append(await self.check_database(db))
        self.checks.append(await self.check_redis())
        self.checks.append(self.check_disk_space())
        self.checks.append(self.check_memory())
        self.checks.append(self.check_cpu())
        self.checks.append(await self.check_workers(db))

        return {
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "checks": self.checks
        }


async def get_health_status(db: AsyncSession) -> Dict[str, Any]:
    """Get comprehensive health status"""
    health_check = HealthCheck()
    return await health_check.run_all_checks(db)
