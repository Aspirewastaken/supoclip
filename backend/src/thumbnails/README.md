# SupoClip Thumbnail Generation System

Automatic thumbnail generation system for creating engaging, click-worthy thumbnails from video content.

## Features

- **Multiple Frame Extraction Methods**: Face detection, motion analysis, composition scoring
- **15+ Pre-defined Styles**: YouTube Premium, MrBeast Style, TikTok Style, and more
- **Text Overlay System**: Emoji support, shadows, glows, backgrounds
- **AI Scoring**: Automatic click-worthiness scoring
- **Multiple Size Outputs**: Generate thumbnails in various sizes (1080x1920, 1280x720, 1920x1080)

## Quick Start

### Basic Usage

```python
from src.thumbnails import generate_thumbnails, FrameExtractionMethod

# Generate thumbnails with default settings
variations = generate_thumbnails(
    video_path="/path/to/video.mp4",
    text="This Changed EVERYTHING!"
)

# Access best thumbnail
best = variations[0]
best.image.save("thumbnail.jpg")
print(f"Score: {best.score}, Method: {best.method.value}, Style: {best.style.name}")
```

### Custom Configuration

```python
from src.thumbnails import (
    generate_thumbnails,
    FrameExtractionMethod,
    score_thumbnails_with_ai
)
from src.thumbnails.styles import get_style_by_name

# Specify extraction methods
methods = [
    FrameExtractionMethod.FACE_CLOSEUP,
    FrameExtractionMethod.HIGH_MOTION,
    FrameExtractionMethod.BEST_COMPOSITION
]

# Choose specific styles
styles = [
    get_style_by_name("youtube_premium"),
    get_style_by_name("mrbeast_style"),
    get_style_by_name("bold_yellow")
]

# Custom sizes
sizes = [
    (1080, 1920),  # Vertical
    (1280, 720),   # HD
    (1920, 1080)   # Full HD
]

# Generate thumbnails
variations = generate_thumbnails(
    video_path="/path/to/video.mp4",
    text="How I Made $10,000 in ONE DAY",
    methods=methods,
    styles=styles,
    start_time=5.0,
    end_time=35.0,
    sizes=sizes
)

# Score with AI
variations = await score_thumbnails_with_ai(
    variations,
    video_title="My Viral Video",
    video_description="Amazing content"
)

# Save top 3 thumbnails
for i, variation in enumerate(variations[:3]):
    variation.image.save(f"thumbnail_{i+1}.jpg")
    print(f"#{i+1}: {variation.method.value} + {variation.style.name} = {variation.score:.2f}")
```

## Frame Extraction Methods

### 1. Face Closeup (`face_closeup`)
Finds frames with the largest, most centered faces. Perfect for talking head content.

**Best for:**
- Interview videos
- Vlogs
- Reaction videos
- Tutorial videos with presenter

### 2. High Motion (`high_motion`)
Finds frames with the most action/movement. Great for dynamic content.

**Best for:**
- Sports clips
- Action sequences
- Dance videos
- Gaming content

### 3. Best Composition (`best_composition`)
Analyzes sharpness, contrast, and brightness to find the best quality frame.

**Best for:**
- Professional content
- Product showcases
- Cinematic videos
- High-quality productions

### 4. Middle Frame (`middle_frame`)
Uses the middle frame of the video/segment. Safe, balanced choice.

**Best for:**
- Generic content
- When other methods fail
- Consistent thumbnail positioning

### 5. First Frame (`first_frame`)
Uses the first frame. Good for branded intros.

**Best for:**
- Videos with designed intro frames
- Consistent branding
- Logo reveals

### 6. Last Frame (`last_frame`)
Uses the last frame. Works for conclusion shots.

**Best for:**
- Call-to-action endings
- Result reveals
- Before/after comparisons

## Thumbnail Styles

### Popular Styles

#### YouTube Premium
Bold white text with red stroke on black background. Professional and attention-grabbing.
```python
style = get_style_by_name("youtube_premium")
```

#### MrBeast Style
Gold text with dark red stroke, heavy shadow and glow. Maximum impact.
```python
style = get_style_by_name("mrbeast_style")
```

#### TikTok Style
Cyan text with pink stroke, glowing effect. Perfect for viral short-form content.
```python
style = get_style_by_name("tiktok_style")
```

#### Bold Yellow
Gold text on black background with shadow. Classic clickbait style.
```python
style = get_style_by_name("bold_yellow")
```

#### Fire Red
Red text with gold stroke, shadow and glow. Urgent, exciting feel.
```python
style = get_style_by_name("fire_red")
```

### All Available Styles

View all styles:
```python
from src.thumbnails.styles import get_all_styles, get_style_names

# Get all style names
print(get_style_names())

# Get all style objects
styles = get_all_styles()
for style in styles:
    print(f"{style.name}: {style.font_color} with {style.stroke_color} stroke")
```

Filter styles:
```python
from src.thumbnails.styles import (
    get_styles_by_position,
    get_styles_with_glow,
    get_styles_with_background
)

# Get styles with text at bottom
bottom_styles = get_styles_by_position("bottom")

# Get styles with glow effect
glow_styles = get_styles_with_glow()

# Get styles with background
bg_styles = get_styles_with_background()
```

## API Endpoints

### POST /thumbnails/generate

Generate thumbnails from video with various styles and extraction methods.

**Request Body:**
```json
{
  "video_path": "/tmp/my_video.mp4",
  "text": "This Changed EVERYTHING!",
  "methods": ["face_closeup", "high_motion", "best_composition"],
  "styles": ["youtube_premium", "mrbeast_style", "bold_yellow"],
  "start_time": 0.0,
  "end_time": 30.0,
  "sizes": [
    {"width": 1080, "height": 1920},
    {"width": 1280, "height": 720}
  ],
  "enable_ai_scoring": true,
  "video_title": "How I Made $10,000",
  "video_description": "My journey to success",
  "return_format": "base64"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully generated 18 thumbnails",
  "thumbnails": [
    {
      "id": "thumb_0",
      "method": "face_closeup",
      "style": "YouTube Premium",
      "timestamp": 15.5,
      "score": 0.92,
      "size": {"width": 1080, "height": 1920},
      "image_data": "base64_encoded_image...",
      "metadata": {
        "face_detected": true,
        "face_count": 1,
        "face_score": 0.85
      }
    }
  ],
  "total_generated": 18,
  "best_thumbnail": {...},
  "generation_time_seconds": 8.5
}
```

### GET /thumbnails/styles

Get all available thumbnail styles with optional filtering.

**Query Parameters:**
- `position` (optional): Filter by text position (top, middle, bottom)
- `with_glow` (optional): Filter styles with glow effect
- `with_background` (optional): Filter styles with background
- `popular_only` (optional): Return only popular styles

**Example:**
```bash
GET /thumbnails/styles?popular_only=true
```

**Response:**
```json
{
  "styles": [
    {
      "name": "YouTube Premium",
      "font_size": 76,
      "font_color": "#FFFFFF",
      "stroke_width": 6,
      "stroke_color": "#FF0000",
      "background_color": "#000000",
      "position": "middle",
      "has_shadow": true,
      "has_glow": false
    }
  ],
  "total": 5
}
```

### GET /thumbnails/methods

Get all available frame extraction methods.

**Response:**
```json
{
  "methods": [
    {
      "value": "face_closeup",
      "name": "Face Closeup",
      "description": "Extracts frame with largest, most centered face - great for talking head content"
    },
    {
      "value": "high_motion",
      "name": "High Motion",
      "description": "Extracts frame with highest motion/action - perfect for dynamic content"
    }
  ],
  "total": 6
}
```

### GET /thumbnails/preview

Preview a thumbnail style without generating from video.

**Query Parameters:**
- `style_name` (required): Style name to preview
- `text` (optional): Text to preview (default: "Preview Text")

**Example:**
```bash
GET /thumbnails/preview?style_name=youtube_premium&text=My%20Video%20Title
```

**Response:** JPEG image

## AI Scoring

The AI scoring system evaluates thumbnails based on:

1. **Visual Appeal**: Color contrast, composition, sharpness
2. **Text Readability**: Font size, contrast, positioning
3. **Emotional Impact**: Facial expressions, action, intrigue
4. **Click-Worthiness**: Would someone stop scrolling?
5. **Context**: How well it represents the video

Scores range from 0.0 (poor) to 1.0 (excellent).

```python
from src.thumbnails import score_thumbnails_with_ai

# Score thumbnails
scored_variations = await score_thumbnails_with_ai(
    variations,
    video_title="My Amazing Video",
    video_description="This is what happened..."
)

# Top 3 thumbnails
for i, var in enumerate(scored_variations[:3]):
    print(f"#{i+1} Score: {var.score:.2f}")
    print(f"   Method: {var.method.value}")
    print(f"   Style: {var.style.name}")
    print(f"   Reasoning: {var.metadata['ai_reasoning']}")
    print(f"   Strengths: {var.metadata['ai_strengths']}")
    print()
```

## Custom Styles

Create custom styles programmatically:

```python
from src.thumbnails import ThumbnailStyle

# Create custom style
custom_style = ThumbnailStyle(
    name="My Custom Style",
    font_size=70,
    font_color="#FF00FF",  # Magenta
    stroke_width=5,
    stroke_color="#FFFFFF",
    background_color="#000000",
    background_opacity=0.7,
    shadow=True,
    glow=True,
    position="middle",
    emoji_size=75,
    padding=40
)

# Use in generation
variations = generate_thumbnails(
    video_path="/path/to/video.mp4",
    text="Check This Out!",
    styles=[custom_style]
)
```

## Performance Tips

1. **Limit extraction methods**: Each method requires frame analysis
   ```python
   # Fast: 1 method
   methods = [FrameExtractionMethod.MIDDLE_FRAME]

   # Slow: All methods
   methods = list(FrameExtractionMethod)
   ```

2. **Reduce style variations**: More styles = more processing
   ```python
   # Fast: 2-3 styles
   styles = get_popular_styles()[:3]

   # Slow: All styles
   styles = get_all_styles()
   ```

3. **Optimize size outputs**: Generate only needed sizes
   ```python
   # Fast: Single size
   sizes = [(1280, 720)]

   # Slower: Multiple sizes
   sizes = [(1080, 1920), (1280, 720), (1920, 1080)]
   ```

4. **Disable AI scoring for drafts**: Skip AI when testing
   ```python
   # Generate without AI scoring
   variations = generate_thumbnails(...)

   # Score only the best ones later
   top_5 = variations[:5]
   scored = await score_thumbnails_with_ai(top_5)
   ```

## Examples

### Example 1: Quick Thumbnail for YouTube Short
```python
variations = generate_thumbnails(
    video_path="/path/to/short.mp4",
    text="Wait for it... 😱",
    methods=[FrameExtractionMethod.HIGH_MOTION],
    styles=[get_style_by_name("tiktok_style")],
    sizes=[(1080, 1920)]
)
variations[0].image.save("short_thumbnail.jpg")
```

### Example 2: A/B Testing Thumbnails
```python
# Generate multiple variations
variations = generate_thumbnails(
    video_path="/path/to/video.mp4",
    text="I Tried This For 30 Days",
    methods=[
        FrameExtractionMethod.FACE_CLOSEUP,
        FrameExtractionMethod.HIGH_MOTION
    ],
    styles=[
        get_style_by_name("youtube_premium"),
        get_style_by_name("mrbeast_style"),
        get_style_by_name("bold_yellow")
    ]
)

# Score and save top 3
scored = await score_thumbnails_with_ai(variations)
for i, var in enumerate(scored[:3]):
    var.image.save(f"ab_test_{i+1}.jpg")
```

### Example 3: Batch Processing
```python
import asyncio
from pathlib import Path

async def process_video(video_path: str):
    variations = generate_thumbnails(
        video_path=video_path,
        text=Path(video_path).stem,  # Use filename as text
        methods=[FrameExtractionMethod.BEST_COMPOSITION]
    )

    scored = await score_thumbnails_with_ai(variations)
    output_path = Path(video_path).with_suffix('.jpg')
    scored[0].image.save(output_path)
    return output_path

# Process multiple videos
video_files = ["/path/to/video1.mp4", "/path/to/video2.mp4"]
results = await asyncio.gather(*[process_video(v) for v in video_files])
print(f"Generated {len(results)} thumbnails")
```

## Troubleshooting

### No faces detected
If face detection fails, the system automatically falls back to middle frame.

**Solutions:**
- Use different extraction methods (high_motion, best_composition)
- Adjust start_time/end_time to include faces
- Check video quality and lighting

### Text not readable
If text is hard to read on the thumbnail:

**Solutions:**
- Use styles with stronger contrast (youtube_premium, dramatic_contrast)
- Use styles with backgrounds (bold_yellow, fire_red)
- Increase font_size in custom style
- Add glow or shadow effects

### AI scoring not working
If AI scoring returns errors:

**Solutions:**
- Check LLM configuration in .env
- Ensure API keys are valid
- Disable AI scoring and manually select thumbnails
- Check AI model quotas

### Memory issues
If generating many thumbnails causes memory issues:

**Solutions:**
- Process in smaller batches
- Reduce number of styles/methods
- Generate fewer size variations
- Use context manager properly:
  ```python
  with ThumbnailGenerator(video_path) as gen:
      # Generate thumbnails
      pass
  # Resources automatically cleaned up
  ```

## Architecture

```
thumbnails/
├── __init__.py          # Package exports
├── generator.py         # Core generation logic
├── styles.py           # Pre-defined styles
└── README.md           # Documentation

Key Classes:
- ThumbnailGenerator: Main generator class
- ThumbnailStyle: Style configuration
- ThumbnailVariation: Generated thumbnail result
- FrameExtractionMethod: Enum of extraction methods
```

## Dependencies

- PIL/Pillow: Image manipulation
- OpenCV (cv2): Video frame extraction, face detection
- MediaPipe: Advanced face detection (optional)
- MoviePy: Video clip handling
- NumPy: Image array operations
- Pydantic AI: AI scoring

## Future Enhancements

- [ ] Vision model integration for direct image scoring
- [ ] Automatic color scheme detection from video
- [ ] Face emotion detection for thumbnail selection
- [ ] Template-based thumbnail generation
- [ ] Batch processing optimization
- [ ] Thumbnail performance analytics integration
