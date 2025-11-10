# Watermarks Directory

This directory contains watermark videos that will be overlaid onto generated clips.

## File Structure

- `default.mp4` - Default watermark used when no account-specific watermark exists
- `{account_id}.mp4` - Account-specific watermark (e.g., `user123.mp4`)
- `metadata.json` - Watermark settings (position, scale, opacity) per account

## Watermark Video Requirements

1. **Format**: MP4 (H.264 codec recommended)
2. **Aspect Ratio**: Any (will be scaled automatically)
3. **Green Screen**: Optional but recommended
   - Use pure green (#00FF00) background for transparency
   - The overlay system will remove green using chromakey
   - Without green screen, the watermark will have a solid background

4. **Recommended Dimensions**:
   - 500x500px or larger for quality
   - Will be scaled to 15% of video width by default

## Creating a Default Watermark

### Option 1: With Green Screen (Recommended)

Create a video with:
- Your logo/text on a pure green (#00FF00) background
- Duration: 1-5 seconds (will loop if needed)
- Resolution: 500x500px or higher

### Option 2: Without Green Screen

If you don't use green screen:
- The watermark will have a solid background
- Use PNG sequence or video with alpha channel for transparency
- Consider semi-transparent backgrounds

## Example FFmpeg Command to Create Test Watermark

```bash
# Create a simple text watermark with green screen
ffmpeg -f lavfi -i color=c=green:s=500x500:d=3 \
  -vf "drawtext=text='SUPOCLIP':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" \
  -c:v libx264 -pix_fmt yuv420p -y default.mp4
```

## Watermark Placement

Default settings (can be customized per account via API):
- **Position**: bottom_right
- **Scale**: 15% of video width
- **Opacity**: 100%

Available positions:
- `top_left`
- `top_right`
- `bottom_left`
- `bottom_right`
- `center`

## API Usage

### Upload Watermark
```bash
POST /watermarks/upload
Content-Type: multipart/form-data

Fields:
- account_id: string (user/account ID)
- watermark: file (MP4 video)
```

### List Watermarks
```bash
GET /watermarks
```

### Delete Watermark
```bash
DELETE /watermarks/{account_id}
```

## Notes

- Watermark files are named by account_id (e.g., `abc123.mp4`)
- If no account-specific watermark exists, `default.mp4` is used
- The watermark system in `src/watermark/overlay.py` handles the actual video compositing
