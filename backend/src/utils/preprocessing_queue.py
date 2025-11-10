"""
Video preprocessing queue system for async video processing.

This module provides a queue-based system for preprocessing videos,
including download, transcription, and AI analysis, before clip generation.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    GENERATING_CLIPS = "generating_clips"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PreprocessingTask:
    """Represents a video preprocessing task."""
    task_id: str
    video_url: str
    user_id: str
    status: TaskStatus = TaskStatus.QUEUED
    progress: float = 0.0  # 0.0 to 100.0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        return {
            'task_id': self.task_id,
            'video_url': self.video_url,
            'user_id': self.user_id,
            'status': self.status.value,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'result_data': self.result_data,
            'metadata': self.metadata
        }


class PreprocessingQueue:
    """
    Queue system for video preprocessing with priority and worker management.
    """

    def __init__(self, max_concurrent_tasks: int = 3):
        """
        Initialize preprocessing queue.

        Args:
            max_concurrent_tasks: Maximum number of tasks to process concurrently
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[str, PreprocessingTask] = {}
        self.completed_tasks: Dict[str, PreprocessingTask] = {}
        self.workers: List[asyncio.Task] = []
        self.is_running = False
        self.task_callbacks: Dict[str, List[Callable]] = {}

        logger.info(f"Preprocessing queue initialized with {max_concurrent_tasks} concurrent workers")

    async def start(self):
        """Start the preprocessing queue workers."""
        if self.is_running:
            logger.warning("Preprocessing queue already running")
            return

        self.is_running = True
        logger.info("Starting preprocessing queue workers")

        # Start worker tasks
        for i in range(self.max_concurrent_tasks):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)

        logger.info(f"Started {len(self.workers)} preprocessing workers")

    async def stop(self):
        """Stop the preprocessing queue workers."""
        if not self.is_running:
            return

        logger.info("Stopping preprocessing queue")
        self.is_running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

        logger.info("Preprocessing queue stopped")

    async def add_task(
        self,
        task_id: str,
        video_url: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> PreprocessingTask:
        """
        Add a preprocessing task to the queue.

        Args:
            task_id: Unique task identifier
            video_url: URL or path to video
            user_id: User ID who created the task
            metadata: Optional metadata for the task
            priority: Task priority (higher = processed first)

        Returns:
            PreprocessingTask object
        """
        task = PreprocessingTask(
            task_id=task_id,
            video_url=video_url,
            user_id=user_id,
            metadata=metadata or {}
        )

        # Add priority to metadata for queue ordering
        task.metadata['priority'] = priority

        await self.queue.put(task)
        logger.info(f"Task {task_id} added to preprocessing queue (priority: {priority})")

        return task

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        # Check active tasks
        if task_id in self.active_tasks:
            return self.active_tasks[task_id].to_dict()

        # Check completed tasks
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id].to_dict()

        # Check queue (slower)
        for item in list(self.queue._queue):
            if item.task_id == task_id:
                return item.to_dict()

        return None

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task if it's still queued or processing."""
        # Check if task is in active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            task.error_message = "Task cancelled by user"
            self.completed_tasks[task_id] = task
            del self.active_tasks[task_id]
            logger.info(f"Cancelled active task {task_id}")
            return True

        # Check queue (remove if found)
        queue_items = []
        found = False
        while not self.queue.empty():
            item = await self.queue.get()
            if item.task_id == task_id:
                item.status = TaskStatus.CANCELLED
                item.completed_at = datetime.now()
                self.completed_tasks[task_id] = item
                found = True
                logger.info(f"Cancelled queued task {task_id}")
            else:
                queue_items.append(item)

        # Re-add non-cancelled items
        for item in queue_items:
            await self.queue.put(item)

        return found

    def register_callback(self, task_id: str, callback: Callable):
        """Register a callback to be called when task completes."""
        if task_id not in self.task_callbacks:
            self.task_callbacks[task_id] = []
        self.task_callbacks[task_id].append(callback)

    async def _worker(self, worker_id: int):
        """Worker coroutine that processes tasks from the queue."""
        logger.info(f"Worker {worker_id} started")

        while self.is_running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(self.queue.get(), timeout=1.0)

                logger.info(f"Worker {worker_id} processing task {task.task_id}")
                task.status = TaskStatus.DOWNLOADING
                task.started_at = datetime.now()
                self.active_tasks[task.task_id] = task

                # Process the task
                try:
                    await self._process_task(task, worker_id)
                except Exception as e:
                    logger.error(f"Worker {worker_id} error processing task {task.task_id}: {e}")
                    task.status = TaskStatus.FAILED
                    task.error_message = str(e)

                # Move to completed
                task.completed_at = datetime.now()
                self.completed_tasks[task.task_id] = task
                if task.task_id in self.active_tasks:
                    del self.active_tasks[task.task_id]

                # Execute callbacks
                if task.task_id in self.task_callbacks:
                    for callback in self.task_callbacks[task.task_id]:
                        try:
                            await callback(task)
                        except Exception as e:
                            logger.error(f"Error executing callback for task {task.task_id}: {e}")
                    del self.task_callbacks[task.task_id]

                self.queue.task_done()

            except asyncio.TimeoutError:
                # No task available, continue loop
                continue
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} unexpected error: {e}")
                continue

        logger.info(f"Worker {worker_id} stopped")

    async def _process_task(self, task: PreprocessingTask, worker_id: int):
        """Process a single preprocessing task."""
        from ..video_utils import get_video_transcript
        from ..ai import get_most_relevant_parts_by_transcript
        from ..youtube_utils import download_youtube_video

        logger.info(f"Worker {worker_id}: Starting preprocessing for task {task.task_id}")

        # Step 1: Download video (if YouTube URL)
        task.status = TaskStatus.DOWNLOADING
        task.progress = 10.0

        video_path = None
        if task.video_url.startswith('http'):
            logger.info(f"Worker {worker_id}: Downloading video from {task.video_url}")
            video_path = download_youtube_video(task.video_url)
            if not video_path:
                raise Exception("Failed to download video")
        else:
            video_path = task.video_url

        task.progress = 30.0

        # Step 2: Transcribe video
        task.status = TaskStatus.TRANSCRIBING
        logger.info(f"Worker {worker_id}: Transcribing video at {video_path}")

        transcript = get_video_transcript(Path(video_path))
        task.progress = 60.0

        # Step 3: AI Analysis
        task.status = TaskStatus.ANALYZING
        logger.info(f"Worker {worker_id}: Analyzing transcript with AI")

        analysis_result = await get_most_relevant_parts_by_transcript(transcript)
        task.progress = 80.0

        # Step 4: Store results
        task.result_data = {
            'video_path': str(video_path),
            'transcript': transcript,
            'segments': [
                {
                    'start_time': seg.start_time,
                    'end_time': seg.end_time,
                    'text': seg.text,
                    'relevance_score': seg.relevance_score,
                    'reasoning': seg.reasoning
                }
                for seg in analysis_result.most_relevant_segments
            ],
            'summary': analysis_result.summary,
            'key_topics': analysis_result.key_topics
        }

        task.status = TaskStatus.COMPLETED
        task.progress = 100.0

        logger.info(f"Worker {worker_id}: Task {task.task_id} preprocessing completed")

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get current queue statistics."""
        return {
            'queue_size': self.queue.qsize(),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'is_running': self.is_running,
            'workers_count': len(self.workers)
        }

    async def clear_completed_tasks(self, max_age_hours: int = 24):
        """Clear completed tasks older than max_age_hours."""
        current_time = datetime.now()
        tasks_to_remove = []

        for task_id, task in self.completed_tasks.items():
            if task.completed_at:
                age_hours = (current_time - task.completed_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.completed_tasks[task_id]

        logger.info(f"Cleared {len(tasks_to_remove)} old completed tasks")


# Global preprocessing queue instance
preprocessing_queue: Optional[PreprocessingQueue] = None


def get_preprocessing_queue(max_concurrent_tasks: int = 3) -> PreprocessingQueue:
    """Get or create global preprocessing queue instance."""
    global preprocessing_queue
    if preprocessing_queue is None:
        preprocessing_queue = PreprocessingQueue(max_concurrent_tasks)
    return preprocessing_queue
