"""
Thumbnail generation system for SupoClip.
Extracts interesting frames, applies text overlays, and generates variations.
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import logging
import asyncio
from dataclasses import dataclass
from enum import Enum

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from moviepy import VideoFileClip

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

from ..config import Config

logger = logging.getLogger(__name__)
config = Config()


class FrameExtractionMethod(Enum):
    """Methods for extracting frames from video."""
    FACE_CLOSEUP = "face_closeup"
    HIGH_MOTION = "high_motion"
    FIRST_FRAME = "first_frame"
    MIDDLE_FRAME = "middle_frame"
    LAST_FRAME = "last_frame"
    BEST_COMPOSITION = "best_composition"


@dataclass
class ThumbnailStyle:
    """Defines a thumbnail text overlay style."""
    name: str
    font_size: int
    font_color: str
    stroke_width: int
    stroke_color: str
    background_color: Optional[str]
    background_opacity: float
    shadow: bool
    glow: bool
    position: str  # "top", "middle", "bottom"
    emoji_size: int
    padding: int


@dataclass
class ThumbnailVariation:
    """Represents a single thumbnail variation."""
    image: Image.Image
    method: FrameExtractionMethod
    style: ThumbnailStyle
    timestamp: float
    score: float
    metadata: Dict[str, Any]


class ThumbnailGenerator:
    """
    Generates thumbnails from video files with various extraction methods and styles.
    """

    def __init__(self, video_path: str):
        """
        Initialize thumbnail generator.

        Args:
            video_path: Path to video file
        """
        self.video_path = Path(video_path)
        self.video_clip = None
        self.face_detector = None
        self.haar_cascade = None

        # Initialize face detection
        if MEDIAPIPE_AVAILABLE:
            try:
                self.face_detector = mp.solutions.face_detection.FaceDetection(
                    model_selection=0,
                    min_detection_confidence=0.5
                )
                logger.info("MediaPipe face detector initialized for thumbnails")
            except Exception as e:
                logger.warning(f"Failed to initialize MediaPipe: {e}")

        # Fallback to OpenCV Haar cascade
        if self.face_detector is None:
            try:
                self.haar_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                logger.info("OpenCV Haar cascade initialized for thumbnails")
            except Exception as e:
                logger.warning(f"Failed to initialize Haar cascade: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.video_clip = VideoFileClip(str(self.video_path))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.video_clip:
            self.video_clip.close()
        if self.face_detector:
            self.face_detector.close()

    def extract_frame_by_method(
        self,
        method: FrameExtractionMethod,
        start_time: float = 0.0,
        end_time: Optional[float] = None
    ) -> Tuple[np.ndarray, float, Dict[str, Any]]:
        """
        Extract a frame using specified method.

        Args:
            method: Frame extraction method
            start_time: Start time for extraction (seconds)
            end_time: End time for extraction (seconds), None = video duration

        Returns:
            Tuple of (frame as numpy array, timestamp, metadata dict)
        """
        if not self.video_clip:
            raise RuntimeError("Video clip not loaded. Use context manager.")

        if end_time is None:
            end_time = self.video_clip.duration

        metadata = {"method": method.value}

        if method == FrameExtractionMethod.FIRST_FRAME:
            timestamp = start_time
            frame = self.video_clip.get_frame(timestamp)
            metadata["position"] = "first"

        elif method == FrameExtractionMethod.MIDDLE_FRAME:
            timestamp = start_time + (end_time - start_time) / 2
            frame = self.video_clip.get_frame(timestamp)
            metadata["position"] = "middle"

        elif method == FrameExtractionMethod.LAST_FRAME:
            timestamp = min(end_time - 0.5, end_time)  # Avoid very last frame
            frame = self.video_clip.get_frame(timestamp)
            metadata["position"] = "last"

        elif method == FrameExtractionMethod.FACE_CLOSEUP:
            frame, timestamp, face_metadata = self._extract_best_face_frame(start_time, end_time)
            metadata.update(face_metadata)

        elif method == FrameExtractionMethod.HIGH_MOTION:
            frame, timestamp, motion_metadata = self._extract_high_motion_frame(start_time, end_time)
            metadata.update(motion_metadata)

        elif method == FrameExtractionMethod.BEST_COMPOSITION:
            frame, timestamp, comp_metadata = self._extract_best_composition_frame(start_time, end_time)
            metadata.update(comp_metadata)

        else:
            raise ValueError(f"Unknown extraction method: {method}")

        return frame, timestamp, metadata

    def _extract_best_face_frame(
        self,
        start_time: float,
        end_time: float
    ) -> Tuple[np.ndarray, float, Dict[str, Any]]:
        """
        Extract frame with best face detection (largest, most centered face).

        Returns:
            Tuple of (frame, timestamp, metadata)
        """
        duration = end_time - start_time
        sample_interval = min(0.5, duration / 20)  # Sample up to 20 frames

        best_frame = None
        best_timestamp = start_time
        best_score = 0
        face_count = 0

        current_time = start_time
        while current_time < end_time:
            try:
                frame = self.video_clip.get_frame(current_time)
                faces = self._detect_faces(frame)

                if faces:
                    # Calculate score based on face size and position
                    height, width = frame.shape[:2]
                    center_x, center_y = width / 2, height / 2

                    for (x, y, w, h, confidence) in faces:
                        face_center_x = x + w / 2
                        face_center_y = y + h / 2

                        # Score: larger faces and centered faces are better
                        size_score = (w * h) / (width * height)  # Normalized face size
                        distance_from_center = np.sqrt(
                            (face_center_x - center_x) ** 2 +
                            (face_center_y - center_y) ** 2
                        )
                        center_score = 1.0 - (distance_from_center / (width / 2))

                        # Combined score
                        score = (size_score * 0.6 + center_score * 0.3 + confidence * 0.1)

                        if score > best_score:
                            best_score = score
                            best_frame = frame
                            best_timestamp = current_time
                            face_count = len(faces)

                current_time += sample_interval

            except Exception as e:
                logger.warning(f"Error extracting face frame at {current_time:.2f}s: {e}")
                current_time += sample_interval
                continue

        if best_frame is None:
            # Fallback to middle frame
            logger.warning("No faces detected, using middle frame as fallback")
            best_timestamp = start_time + duration / 2
            best_frame = self.video_clip.get_frame(best_timestamp)

        metadata = {
            "face_detected": best_score > 0,
            "face_count": face_count,
            "face_score": float(best_score)
        }

        return best_frame, best_timestamp, metadata

    def _extract_high_motion_frame(
        self,
        start_time: float,
        end_time: float
    ) -> Tuple[np.ndarray, float, Dict[str, Any]]:
        """
        Extract frame with highest motion (frame difference).

        Returns:
            Tuple of (frame, timestamp, metadata)
        """
        duration = end_time - start_time
        sample_interval = min(0.5, duration / 20)

        prev_frame = None
        best_frame = None
        best_timestamp = start_time
        max_motion = 0

        current_time = start_time
        while current_time < end_time:
            try:
                frame = self.video_clip.get_frame(current_time)

                if prev_frame is not None:
                    # Calculate motion as frame difference
                    gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_RGB2GRAY)
                    gray2 = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

                    diff = cv2.absdiff(gray1, gray2)
                    motion = np.mean(diff)

                    if motion > max_motion:
                        max_motion = motion
                        best_frame = frame
                        best_timestamp = current_time

                prev_frame = frame
                current_time += sample_interval

            except Exception as e:
                logger.warning(f"Error calculating motion at {current_time:.2f}s: {e}")
                current_time += sample_interval
                continue

        if best_frame is None:
            # Fallback to middle frame
            best_timestamp = start_time + duration / 2
            best_frame = self.video_clip.get_frame(best_timestamp)

        metadata = {
            "max_motion": float(max_motion),
            "motion_score": float(max_motion / 255.0)  # Normalized
        }

        return best_frame, best_timestamp, metadata

    def _extract_best_composition_frame(
        self,
        start_time: float,
        end_time: float
    ) -> Tuple[np.ndarray, float, Dict[str, Any]]:
        """
        Extract frame with best composition (rule of thirds, contrast, sharpness).

        Returns:
            Tuple of (frame, timestamp, metadata)
        """
        duration = end_time - start_time
        sample_interval = min(0.5, duration / 20)

        best_frame = None
        best_timestamp = start_time
        best_score = 0

        current_time = start_time
        while current_time < end_time:
            try:
                frame = self.video_clip.get_frame(current_time)

                # Calculate composition score
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

                # Sharpness (Laplacian variance)
                sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()

                # Contrast (standard deviation)
                contrast = np.std(gray)

                # Brightness balance (not too dark, not too bright)
                mean_brightness = np.mean(gray)
                brightness_score = 1.0 - abs(mean_brightness - 128) / 128

                # Combined score
                score = (
                    (sharpness / 1000) * 0.4 +  # Normalized sharpness
                    (contrast / 100) * 0.3 +     # Normalized contrast
                    brightness_score * 0.3
                )

                if score > best_score:
                    best_score = score
                    best_frame = frame
                    best_timestamp = current_time

                current_time += sample_interval

            except Exception as e:
                logger.warning(f"Error analyzing composition at {current_time:.2f}s: {e}")
                current_time += sample_interval
                continue

        if best_frame is None:
            best_timestamp = start_time + duration / 2
            best_frame = self.video_clip.get_frame(best_timestamp)

        metadata = {
            "composition_score": float(best_score)
        }

        return best_frame, best_timestamp, metadata

    def _detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Detect faces in frame using available detectors.

        Returns:
            List of (x, y, width, height, confidence) tuples
        """
        faces = []

        # Try MediaPipe first
        if self.face_detector is not None:
            try:
                results = self.face_detector.process(frame)

                if results.detections:
                    height, width = frame.shape[:2]
                    for detection in results.detections:
                        bbox = detection.location_data.relative_bounding_box
                        confidence = detection.score[0]

                        x = int(bbox.xmin * width)
                        y = int(bbox.ymin * height)
                        w = int(bbox.width * width)
                        h = int(bbox.height * height)

                        faces.append((x, y, w, h, confidence))

                    return faces
            except Exception as e:
                logger.debug(f"MediaPipe face detection failed: {e}")

        # Fallback to Haar cascade
        if self.haar_cascade is not None:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                detected = self.haar_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )

                for (x, y, w, h) in detected:
                    faces.append((x, y, w, h, 0.8))  # Default confidence

            except Exception as e:
                logger.debug(f"Haar cascade detection failed: {e}")

        return faces

    def apply_text_overlay(
        self,
        frame: np.ndarray,
        text: str,
        style: ThumbnailStyle,
        fonts_dir: Optional[Path] = None
    ) -> Image.Image:
        """
        Apply text overlay to frame using specified style.

        Args:
            frame: Video frame as numpy array (RGB)
            text: Text to overlay
            style: Thumbnail style configuration
            fonts_dir: Directory containing font files

        Returns:
            PIL Image with text overlay
        """
        # Convert to PIL Image
        img = Image.fromarray(frame)
        width, height = img.size

        # Create drawing context
        draw = ImageDraw.Draw(img)

        # Load font
        if fonts_dir is None:
            fonts_dir = Path(__file__).parent.parent.parent / "fonts"

        font_path = fonts_dir / "TikTokSans-Regular.ttf"
        if not font_path.exists():
            font_path = fonts_dir / "THEBOLDFONT-FREEVERSION.ttf"

        try:
            font = ImageFont.truetype(str(font_path), style.font_size)
        except Exception as e:
            logger.warning(f"Failed to load font: {e}, using default")
            font = ImageFont.load_default()

        # Split text into lines if needed
        lines = self._wrap_text(text, font, width - style.padding * 2, draw)

        # Calculate text position
        if style.position == "top":
            y = style.padding
        elif style.position == "middle":
            # Calculate total height
            total_height = sum([draw.textbbox((0, 0), line, font=font)[3] -
                              draw.textbbox((0, 0), line, font=font)[1]
                              for line in lines])
            y = (height - total_height) // 2
        else:  # bottom
            total_height = sum([draw.textbbox((0, 0), line, font=font)[3] -
                              draw.textbbox((0, 0), line, font=font)[1]
                              for line in lines])
            y = height - total_height - style.padding

        # Create new image with effects if needed
        if style.background_color or style.glow or style.shadow:
            # Create layer for effects
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)

            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (width - text_width) // 2

                # Draw background if specified
                if style.background_color:
                    bg_padding = 10
                    bg_color = self._hex_to_rgba(style.background_color, style.background_opacity)
                    overlay_draw.rectangle(
                        [x - bg_padding, y - bg_padding,
                         x + text_width + bg_padding, y + text_height + bg_padding],
                        fill=bg_color
                    )

                # Draw shadow if specified
                if style.shadow:
                    shadow_offset = 3
                    overlay_draw.text(
                        (x + shadow_offset, y + shadow_offset),
                        line,
                        font=font,
                        fill=(0, 0, 0, 180),
                        stroke_width=style.stroke_width,
                        stroke_fill=(0, 0, 0, 200)
                    )

                # Draw glow if specified
                if style.glow:
                    for offset in range(1, 4):
                        glow_alpha = 100 - offset * 25
                        overlay_draw.text(
                            (x, y),
                            line,
                            font=font,
                            fill=(*self._hex_to_rgb(style.font_color), glow_alpha),
                            stroke_width=style.stroke_width + offset,
                            stroke_fill=(*self._hex_to_rgb(style.stroke_color), glow_alpha)
                        )

                y += text_height + 5

            # Composite overlay onto image
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay)

        # Draw main text
        y = style.padding if style.position == "top" else y
        if style.position == "middle":
            total_height = sum([draw.textbbox((0, 0), line, font=font)[3] -
                              draw.textbbox((0, 0), line, font=font)[1]
                              for line in lines])
            y = (height - total_height) // 2
        elif style.position == "bottom":
            total_height = sum([draw.textbbox((0, 0), line, font=font)[3] -
                              draw.textbbox((0, 0), line, font=font)[1]
                              for line in lines])
            y = height - total_height - style.padding

        img = img.convert('RGB')
        draw = ImageDraw.Draw(img)

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2

            draw.text(
                (x, y),
                line,
                font=font,
                fill=style.font_color,
                stroke_width=style.stroke_width,
                stroke_fill=style.stroke_color
            )

            y += text_height + 5

        return img

    def _wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
        draw: ImageDraw.ImageDraw
    ) -> List[str]:
        """Wrap text to fit within max width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _hex_to_rgba(self, hex_color: str, alpha: float) -> Tuple[int, int, int, int]:
        """Convert hex color and alpha to RGBA tuple."""
        rgb = self._hex_to_rgb(hex_color)
        return (*rgb, int(alpha * 255))

    def generate_variations(
        self,
        text: str,
        methods: List[FrameExtractionMethod],
        styles: List[ThumbnailStyle],
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        sizes: Optional[List[Tuple[int, int]]] = None
    ) -> List[ThumbnailVariation]:
        """
        Generate multiple thumbnail variations.

        Args:
            text: Text to overlay on thumbnails
            methods: List of frame extraction methods to use
            styles: List of styles to apply
            start_time: Start time for frame extraction
            end_time: End time for frame extraction
            sizes: List of (width, height) tuples for output sizes

        Returns:
            List of ThumbnailVariation objects
        """
        if sizes is None:
            sizes = [(1080, 1920), (1280, 720), (1920, 1080)]  # Vertical, HD, Full HD

        variations = []

        for method in methods:
            try:
                # Extract frame
                frame, timestamp, metadata = self.extract_frame_by_method(
                    method, start_time, end_time
                )

                for style in styles:
                    try:
                        # Apply text overlay
                        thumbnail = self.apply_text_overlay(frame, text, style)

                        # Generate different sizes
                        for width, height in sizes:
                            resized = thumbnail.copy()
                            resized.thumbnail((width, height), Image.Resampling.LANCZOS)

                            # Create final image with exact dimensions
                            final = Image.new('RGB', (width, height), (0, 0, 0))
                            # Center the thumbnail
                            x = (width - resized.width) // 2
                            y = (height - resized.height) // 2
                            final.paste(resized, (x, y))

                            variation = ThumbnailVariation(
                                image=final,
                                method=method,
                                style=style,
                                timestamp=timestamp,
                                score=0.0,  # Will be scored later
                                metadata={
                                    **metadata,
                                    "size": (width, height),
                                    "style_name": style.name
                                }
                            )

                            variations.append(variation)
                            logger.info(
                                f"Generated thumbnail: {method.value} + {style.name} @ "
                                f"{timestamp:.2f}s ({width}x{height})"
                            )

                    except Exception as e:
                        logger.error(f"Error applying style {style.name}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error extracting frame with method {method.value}: {e}")
                continue

        return variations


# Helper functions

def extract_interesting_frames(
    video_path: str,
    methods: Optional[List[FrameExtractionMethod]] = None,
    start_time: float = 0.0,
    end_time: Optional[float] = None
) -> List[Tuple[np.ndarray, float, Dict[str, Any]]]:
    """
    Extract interesting frames from video.

    Args:
        video_path: Path to video file
        methods: List of extraction methods (default: all methods)
        start_time: Start time in seconds
        end_time: End time in seconds

    Returns:
        List of (frame, timestamp, metadata) tuples
    """
    if methods is None:
        methods = [
            FrameExtractionMethod.FACE_CLOSEUP,
            FrameExtractionMethod.HIGH_MOTION,
            FrameExtractionMethod.BEST_COMPOSITION,
            FrameExtractionMethod.MIDDLE_FRAME
        ]

    frames = []

    with ThumbnailGenerator(video_path) as generator:
        for method in methods:
            try:
                frame, timestamp, metadata = generator.extract_frame_by_method(
                    method, start_time, end_time
                )
                frames.append((frame, timestamp, metadata))
            except Exception as e:
                logger.error(f"Error extracting frame with {method.value}: {e}")
                continue

    return frames


def generate_thumbnails(
    video_path: str,
    text: str,
    methods: Optional[List[FrameExtractionMethod]] = None,
    styles: Optional[List[ThumbnailStyle]] = None,
    start_time: float = 0.0,
    end_time: Optional[float] = None,
    sizes: Optional[List[Tuple[int, int]]] = None
) -> List[ThumbnailVariation]:
    """
    Generate thumbnails with text overlays.

    Args:
        video_path: Path to video file
        text: Text to overlay
        methods: Frame extraction methods
        styles: Text overlay styles
        start_time: Start time for extraction
        end_time: End time for extraction
        sizes: Output sizes

    Returns:
        List of thumbnail variations
    """
    from .styles import get_all_styles

    if methods is None:
        methods = [
            FrameExtractionMethod.FACE_CLOSEUP,
            FrameExtractionMethod.HIGH_MOTION,
            FrameExtractionMethod.BEST_COMPOSITION
        ]

    if styles is None:
        styles = get_all_styles()[:3]  # Use first 3 styles

    with ThumbnailGenerator(video_path) as generator:
        variations = generator.generate_variations(
            text=text,
            methods=methods,
            styles=styles,
            start_time=start_time,
            end_time=end_time,
            sizes=sizes
        )

    return variations


async def score_thumbnails_with_ai(
    variations: List[ThumbnailVariation],
    video_title: Optional[str] = None,
    video_description: Optional[str] = None
) -> List[ThumbnailVariation]:
    """
    Score thumbnails for click-worthiness using AI.

    Args:
        variations: List of thumbnail variations
        video_title: Optional video title for context
        video_description: Optional video description for context

    Returns:
        List of variations with updated scores (sorted by score)
    """
    from pydantic_ai import Agent
    from pydantic import BaseModel

    class ThumbnailScore(BaseModel):
        """Thumbnail click-worthiness score."""
        score: float  # 0.0 to 1.0
        reasoning: str
        strengths: List[str]
        improvements: List[str]

    # Create AI agent for scoring
    scoring_prompt = """You are an expert at evaluating YouTube/social media thumbnail effectiveness.

    Evaluate thumbnails based on:
    1. VISUAL APPEAL: Color contrast, composition, sharpness
    2. TEXT READABILITY: Font size, contrast, positioning
    3. EMOTIONAL IMPACT: Facial expressions, action, intrigue
    4. CLICK-WORTHINESS: Would someone stop scrolling and click?
    5. CONTEXT: How well it represents the video content

    Rate from 0.0 (poor) to 1.0 (excellent) for social media engagement."""

    scoring_agent = Agent(
        model=config.llm,
        result_type=ThumbnailScore,
        system_prompt=scoring_prompt
    )

    # Score each variation
    for variation in variations:
        try:
            # Build context
            context_parts = []
            if video_title:
                context_parts.append(f"Video Title: {video_title}")
            if video_description:
                context_parts.append(f"Description: {video_description}")

            context_parts.extend([
                f"Extraction Method: {variation.method.value}",
                f"Style: {variation.style.name}",
                f"Timestamp: {variation.timestamp:.2f}s",
                f"Metadata: {variation.metadata}"
            ])

            context = "\n".join(context_parts)

            # Note: In a real implementation, you'd pass the image to a vision model
            # For now, we'll score based on metadata
            result = await scoring_agent.run(
                f"""Score this thumbnail variation for click-worthiness:

{context}

Provide a score from 0.0 to 1.0 and explain your reasoning."""
            )

            score_data = result.data
            variation.score = score_data.score
            variation.metadata["ai_score"] = score_data.score
            variation.metadata["ai_reasoning"] = score_data.reasoning
            variation.metadata["ai_strengths"] = score_data.strengths
            variation.metadata["ai_improvements"] = score_data.improvements

            logger.info(
                f"Scored thumbnail ({variation.method.value}, {variation.style.name}): "
                f"{score_data.score:.2f} - {score_data.reasoning[:50]}..."
            )

        except Exception as e:
            logger.error(f"Error scoring thumbnail: {e}")
            variation.score = 0.5  # Default neutral score

    # Sort by score (highest first)
    variations.sort(key=lambda v: v.score, reverse=True)

    return variations
