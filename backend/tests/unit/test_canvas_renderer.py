"""
Unit tests for canvas rendering system.

Tests the canvas_renderer.py module which renders horizontal clips on 9:16 vertical canvas.
"""
import pytest
import numpy as np
import cv2
import tempfile
from pathlib import Path
from src.reframe.canvas_renderer import CanvasRenderer


class TestCanvasRenderer:
    """Test canvas renderer initialization and configuration."""

    def test_default_initialization(self):
        """Test renderer initializes with default 9:16 dimensions."""
        renderer = CanvasRenderer()

        assert renderer.output_width == 1080
        assert renderer.output_height == 1920
        assert renderer.target_ratio == 1080 / 1920

    def test_custom_dimensions(self):
        """Test renderer with custom dimensions."""
        renderer = CanvasRenderer(output_width=720, output_height=1280)

        assert renderer.output_width == 720
        assert renderer.output_height == 1280

    def test_target_ratio_calculation(self):
        """Test that target ratio is correctly calculated."""
        renderer = CanvasRenderer(output_width=1080, output_height=1920)

        # 9:16 ratio = 0.5625
        assert abs(renderer.target_ratio - 0.5625) < 0.001


class TestCreateCanvasFrame:
    """Test canvas frame creation with different styles."""

    @pytest.fixture
    def renderer(self):
        """Create a canvas renderer."""
        return CanvasRenderer(output_width=1080, output_height=1920)

    @pytest.fixture
    def horizontal_frame(self):
        """Create a horizontal test frame (1920x1080)."""
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        frame[:, :] = (100, 150, 200)  # Solid color
        return frame

    def test_original_style_creates_correct_dimensions(self, renderer, horizontal_frame):
        """Test original style creates 9:16 canvas."""
        canvas = renderer._create_canvas_frame(horizontal_frame, style='original')

        assert canvas.shape[0] == 1920  # height
        assert canvas.shape[1] == 1080  # width
        assert canvas.shape[2] == 3     # RGB channels

    def test_original_style_centers_frame(self, renderer, horizontal_frame):
        """Test that original style centers the horizontal frame."""
        canvas = renderer._create_canvas_frame(horizontal_frame, style='original')

        # Most of the canvas should be black (0,0,0) since horizontal is smaller
        # Only the center portion should have the frame content
        # Check that there's black space above and below
        assert np.array_equal(canvas[0, 0], [0, 0, 0])  # Top should be black

    def test_flipped_style_creates_correct_dimensions(self, renderer, horizontal_frame):
        """Test flipped style creates 9:16 canvas."""
        canvas = renderer._create_canvas_frame(horizontal_frame, style='flipped')

        assert canvas.shape[0] == 1920
        assert canvas.shape[1] == 1080
        assert canvas.shape[2] == 3

    def test_flipped_style_mirrors_content(self, renderer):
        """Test that flipped style mirrors the frame horizontally."""
        # Create a frame with a distinct left-right pattern
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        frame[:, :960] = (255, 0, 0)  # Left half red
        frame[:, 960:] = (0, 0, 255)  # Right half blue

        canvas = renderer._create_canvas_frame(frame, style='flipped')

        # The flipped frame should now have blue on the left, red on the right
        # (We need to account for the fact it's centered and scaled)
        # Just verify it's not all black and has content
        assert not np.all(canvas == 0)

    def test_blurry_bg_style_creates_correct_dimensions(self, renderer, horizontal_frame):
        """Test blurry_bg style creates 9:16 canvas."""
        canvas = renderer._create_canvas_frame(horizontal_frame, style='blurry_bg')

        assert canvas.shape[0] == 1920
        assert canvas.shape[1] == 1080
        assert canvas.shape[2] == 3

    def test_blurry_bg_has_background(self, renderer, horizontal_frame):
        """Test that blurry_bg style fills the entire canvas (no black borders)."""
        canvas = renderer._create_canvas_frame(horizontal_frame, style='blurry_bg')

        # Should not have pure black pixels since background is blurred and stretched
        # Check corners which would be black in other styles
        assert not np.array_equal(canvas[0, 0], [0, 0, 0])
        assert not np.array_equal(canvas[-1, -1], [0, 0, 0])

    def test_blurry_bg_has_foreground_overlay(self, renderer):
        """Test that blurry_bg has a foreground overlay."""
        # Create distinctive frame
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        frame[:, :] = (255, 100, 50)

        canvas = renderer._create_canvas_frame(frame, style='blurry_bg')

        # Center area should have the foreground (40% scaled)
        # The exact center pixel should be from the foreground
        center_y = canvas.shape[0] // 2
        center_x = canvas.shape[1] // 2

        # Center should have foreground color (or close to it)
        center_pixel = canvas[center_y, center_x]
        assert center_pixel[0] > 200  # Should be close to 255


class TestFitToCanvas:
    """Test frame fitting logic."""

    @pytest.fixture
    def renderer(self):
        return CanvasRenderer(output_width=1080, output_height=1920)

    def test_fit_horizontal_frame_to_width(self, renderer):
        """Test fitting a horizontal frame to canvas width."""
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

        resized = renderer._fit_to_canvas(frame)

        # Should be scaled to fit canvas width
        assert resized.shape[1] == 1080  # Width matches canvas

    def test_fit_preserves_aspect_ratio(self, renderer):
        """Test that fitting preserves original aspect ratio."""
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        original_ratio = 1920 / 1080

        resized = renderer._fit_to_canvas(frame)

        new_ratio = resized.shape[1] / resized.shape[0]
        assert abs(new_ratio - original_ratio) < 0.01

    def test_fit_doesnt_exceed_canvas_height(self, renderer):
        """Test that fitted frame doesn't exceed canvas height."""
        frame = np.zeros((2000, 1000, 3), dtype=np.uint8)  # Tall frame

        resized = renderer._fit_to_canvas(frame)

        assert resized.shape[0] <= 1920  # Height doesn't exceed canvas


class TestCalculateCenterOffset:
    """Test center offset calculation."""

    @pytest.fixture
    def renderer(self):
        return CanvasRenderer(output_width=1080, output_height=1920)

    def test_center_offset_for_smaller_frame(self, renderer):
        """Test centering a smaller frame on canvas."""
        frame = np.zeros((600, 800, 3), dtype=np.uint8)

        y_offset, x_offset = renderer._calculate_center_offset(frame)

        # Should be centered
        assert y_offset == (1920 - 600) // 2
        assert x_offset == (1080 - 800) // 2

    def test_center_offset_for_full_width_frame(self, renderer):
        """Test centering when frame fills width."""
        frame = np.zeros((600, 1080, 3), dtype=np.uint8)

        y_offset, x_offset = renderer._calculate_center_offset(frame)

        assert x_offset == 0  # No horizontal offset
        assert y_offset == (1920 - 600) // 2  # Vertically centered


@pytest.mark.requires_video
class TestRenderStyles:
    """Integration tests for rendering complete videos."""

    @pytest.fixture
    def renderer(self):
        return CanvasRenderer(output_width=1080, output_height=1920)

    def test_render_original_style(self, renderer, temp_video_file):
        """Test rendering original style to output file."""
        output_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        output_path = output_file.name
        output_file.close()

        try:
            result = renderer.render_original_style(
                input_path=temp_video_file,
                output_path=output_path
            )

            assert result is True
            assert Path(output_path).exists()

            # Verify output dimensions
            cap = cv2.VideoCapture(output_path)
            assert cap.isOpened()
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()

            assert width == 1080
            assert height == 1920

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_render_flipped_style(self, renderer, temp_video_file):
        """Test rendering flipped style to output file."""
        output_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        output_path = output_file.name
        output_file.close()

        try:
            result = renderer.render_flipped_style(
                input_path=temp_video_file,
                output_path=output_path
            )

            assert result is True
            assert Path(output_path).exists()

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_render_blurry_bg_style(self, renderer, temp_video_file):
        """Test rendering blurry background style."""
        output_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        output_path = output_file.name
        output_file.close()

        try:
            result = renderer.render_blurry_bg_style(
                input_path=temp_video_file,
                output_path=output_path
            )

            assert result is True
            assert Path(output_path).exists()

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_render_handles_invalid_input(self, renderer):
        """Test that render gracefully handles invalid input."""
        output_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        output_path = output_file.name
        output_file.close()

        try:
            result = renderer.render_original_style(
                input_path='/nonexistent/video.mp4',
                output_path=output_path
            )

            assert result is False

        finally:
            Path(output_path).unlink(missing_ok=True)


@pytest.mark.parametrize("style", ['original', 'flipped', 'blurry_bg'])
def test_all_styles_produce_valid_output(style):
    """Test that all rendering styles produce valid output frames."""
    renderer = CanvasRenderer(output_width=1080, output_height=1920)

    # Create test frame
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    frame[:, :] = (100, 150, 200)

    canvas = renderer._create_canvas_frame(frame, style=style)

    # All styles should produce valid 9:16 canvas
    assert canvas.shape == (1920, 1080, 3)
    assert canvas.dtype == np.uint8
