# SupoClip Font Management System - Setup Guide

## Overview

SupoClip now includes a comprehensive font management system for captions and title cards. This guide covers setup, usage, and API integration.

## System Components

### 1. Font Directory Structure
```
backend/
├── fonts/
│   ├── fonts.json                    # Font metadata manifest
│   ├── README.md                      # Detailed font documentation
│   ├── download_fonts.sh              # Automated font downloader
│   ├── THEBOLDFONT-FREEVERSION.ttf   # Pre-installed (default fallback)
│   └── TikTokSans-Regular.ttf        # Pre-installed (default)
```

### 2. Code Components

**Font Validation** (`backend/src/video_utils.py`):
- `get_available_fonts()` - List all installed fonts
- `validate_font(font_family)` - Validate font with fallback
- `load_font_metadata(font_family)` - Load metadata from fonts.json
- `VideoProcessor.__init__()` - Enhanced with font validation

**API Endpoints** (`backend/src/api/routes/media.py`):
- `GET /fonts` - List all fonts with metadata and installation status
- `GET /fonts/{font_name}` - Download specific font file

**Caption System** (`backend/src/captions/generator.py`):
- `CaptionGenerator.__init__()` - Enhanced with font validation

**Title Cards** (`backend/src/titlecards/generator.py`):
- `TitleCardGenerator._get_valid_font_path()` - Font validation helper
- All title generation methods updated with validation

## Quick Start

### Option 1: Use Pre-installed Fonts

SupoClip ships with 2 fonts ready to use:
- **TikTokSans-Regular** (default)
- **THEBOLDFONT-FREEVERSION** (fallback)

No setup required - these work out of the box!

### Option 2: Download Recommended Fonts

Download 5 high-quality open-source fonts (Proxima Nova alternatives):

```bash
cd backend/fonts
./download_fonts.sh
```

This installs:
1. **Montserrat-Bold** - Best Proxima Nova alternative
2. **Inter-Bold** - Best for readability
3. **Poppins-Bold** - Best for social media
4. **Roboto-Bold** - Universal compatibility
5. **OpenSans-Bold** - Maximum legibility

### Option 3: Add Custom Fonts

1. Copy your `.ttf` font file to `backend/fonts/`
2. Name it clearly: `MyFont-Bold.ttf`
3. Restart the backend
4. Use it in API requests

## API Usage

### List Available Fonts

**Request:**
```bash
GET http://localhost:8000/fonts
```

**Response:**
```json
{
  "fonts": [
    {
      "id": "tiktoksans-regular",
      "name": "TikTokSans-Regular",
      "display_name": "TikTok Sans",
      "family": "TikTok Sans",
      "category": "sans-serif",
      "style": "regular",
      "weights": [400],
      "variants": ["regular"],
      "file": "TikTokSans-Regular.ttf",
      "license": "TikTok proprietary (use with caution)",
      "description": "The official TikTok font, instantly recognizable for social media content",
      "recommended_for": ["captions", "social-media"],
      "recommended_size": {
        "min": 20,
        "max": 48,
        "default": 32
      },
      "preview_text": "TikTok Style",
      "installed": true,
      "available": true,
      "download_url_api": "/fonts/TikTokSans-Regular"
    },
    {
      "id": "montserrat-bold",
      "name": "Montserrat-Bold",
      "display_name": "Montserrat Bold",
      "family": "Montserrat",
      "category": "sans-serif",
      "style": "bold",
      "description": "A geometric sans-serif inspired by urban typography, excellent for modern content",
      "recommended_for": ["captions", "titles", "social-media"],
      "recommended_size": {
        "min": 24,
        "max": 64,
        "default": 40
      },
      "download_url": "https://fonts.google.com/specimen/Montserrat",
      "alternative_to": "Proxima Nova",
      "installed": false,
      "available": false
    }
  ],
  "summary": {
    "total": 7,
    "installed": 2,
    "available_to_download": 5
  },
  "metadata": {
    "version": "1.0.0",
    "last_updated": "2025-11-10",
    "default_font": "TikTokSans-Regular",
    "fallback_font": "THEBOLDFONT-FREEVERSION"
  }
}
```

**Key Fields:**
- `installed: true` - Font is available to use
- `installed: false` - Font needs to be downloaded
- `recommended_size` - Optimal size range for this font
- `recommended_for` - Use cases (captions, titles, social-media, etc.)
- `alternative_to` - Which premium font this replaces

### Download Font File

**Request:**
```bash
GET http://localhost:8000/fonts/TikTokSans-Regular
```

**Response:**
- Content-Type: `font/ttf`
- Returns the `.ttf` file for client-side preview

### Use Font in Video Processing

**Request:**
```bash
POST http://localhost:8000/start
Content-Type: application/json

{
  "source": {
    "url": "https://youtube.com/watch?v=..."
  },
  "font_options": {
    "font_family": "Montserrat-Bold",
    "font_size": 40,
    "font_color": "#FFFFFF"
  }
}
```

**Font Options:**
- `font_family` - Font name without `.ttf` extension (e.g., "Montserrat-Bold")
- `font_size` - Size in pixels (20-72 recommended)
- `font_color` - Hex color code (e.g., "#FFFFFF", "#FF0000")

**Default Values:**
- `font_family`: "TikTokSans-Regular"
- `font_size`: 24 (or recommended size from fonts.json)
- `font_color`: "#FFFFFF"

## Font Validation & Fallback

The system automatically validates fonts and falls back gracefully:

### Validation Process

1. **Check requested font exists**
   - If yes: Use it
   - If no: Try fallbacks

2. **Fallback order:**
   - TikTokSans-Regular (default)
   - THEBOLDFONT-FREEVERSION (secondary)
   - System default font (last resort)

3. **Logging:**
   - ✅ Info: Font validated and loaded
   - ⚠️ Warning: Font not found, using fallback
   - ❌ Error: No fonts available

### Example Logs

**Successful font load:**
```
INFO: Using font: Montserrat-Bold at /app/fonts/Montserrat-Bold.ttf
```

**Font not found (fallback used):**
```
WARNING: Font 'ProximaNova-Regular' not found. Using fallback: 'TikTokSans-Regular'.
Available fonts: Montserrat-Bold, TikTokSans-Regular, THEBOLDFONT-FREEVERSION
```

**No fonts available (error):**
```
ERROR: No fonts found in /app/fonts. Please install fonts first.
```

## Font Metadata (fonts.json)

The `fonts.json` manifest provides rich metadata for each font:

### Metadata Fields

```json
{
  "id": "montserrat-bold",
  "name": "Montserrat-Bold",
  "display_name": "Montserrat Bold",
  "family": "Montserrat",
  "category": "sans-serif",
  "style": "bold",
  "weights": [700],
  "variants": ["bold"],
  "file": "Montserrat-Bold.ttf",
  "license": "SIL Open Font License",
  "description": "A geometric sans-serif inspired by urban typography",
  "recommended_for": ["captions", "titles", "social-media"],
  "recommended_size": {
    "min": 24,
    "max": 64,
    "default": 40
  },
  "preview_text": "Modern & Clean",
  "download_url": "https://fonts.google.com/specimen/Montserrat",
  "alternative_to": "Proxima Nova",
  "installed": false
}
```

**Use Cases:**
- **Frontend:** Display font picker with previews and metadata
- **Backend:** Apply recommended sizes automatically
- **Documentation:** Show users which fonts work best for what

## Frontend Integration

### Building a Font Picker

```typescript
// Fetch available fonts
const response = await fetch('http://localhost:8000/fonts');
const data = await response.json();

// Filter installed fonts only
const installedFonts = data.fonts.filter(f => f.installed);

// Render font picker
installedFonts.map(font => ({
  value: font.name,
  label: font.display_name,
  preview: font.preview_text,
  recommended: font.recommended_for,
  defaultSize: font.recommended_size.default
}));
```

### Using Font with Video Processing

```typescript
const processVideo = async (youtubeUrl: string, fontFamily: string) => {
  const response = await fetch('http://localhost:8000/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source: { url: youtubeUrl },
      font_options: {
        font_family: fontFamily,
        font_size: 40,
        font_color: '#FFFFFF'
      }
    })
  });

  return response.json();
};
```

## Production Deployment

### Docker Considerations

**Fonts in Docker containers:**

1. Fonts are mounted at `/app/fonts` in containers
2. Make sure `backend/fonts/` is included in your Docker image
3. Or mount fonts directory as a volume:

```yaml
# docker-compose.yml
services:
  backend:
    volumes:
      - ./backend/fonts:/app/fonts:ro
```

### Font Licensing for Commercial Use

**Safe for commercial use (pre-vetted):**
- ✅ Montserrat (SIL Open Font License)
- ✅ Inter (SIL Open Font License)
- ✅ Poppins (SIL Open Font License)
- ✅ Roboto (Apache License 2.0)
- ✅ Open Sans (SIL Open Font License)
- ✅ THEBOLDFONT-FREEVERSION (Free for commercial use)

**Use with caution:**
- ⚠️ TikTokSans-Regular (Proprietary, TikTok brand)

**Not included (requires license):**
- ❌ Proxima Nova (Commercial license required)

### Downloading Fonts in Production

**Option 1: Pre-install during build**
```dockerfile
# Dockerfile
COPY backend/fonts/ /app/fonts/
RUN cd /app/fonts && ./download_fonts.sh
```

**Option 2: Manual download**
```bash
docker exec -it supoclip-backend bash
cd /app/fonts
./download_fonts.sh
```

**Option 3: Volume mount**
```bash
# Download on host
cd backend/fonts
./download_fonts.sh

# Mount in container (via docker-compose.yml)
volumes:
  - ./backend/fonts:/app/fonts:ro
```

## Troubleshooting

### Font not rendering

**Issue:** Font appears broken or uses default font

**Solutions:**
1. Verify font is installed: `ls backend/fonts/*.ttf`
2. Check font name matches exactly (case-sensitive)
3. Verify `.ttf` format (not `.otf`, `.woff`, etc.)
4. Check backend logs for font validation warnings
5. Test font on your system first

### Font API returns empty list

**Issue:** `GET /fonts` returns `{"fonts": []}`

**Solutions:**
1. Check fonts directory exists: `ls backend/fonts/`
2. Ensure at least one `.ttf` file is present
3. Restart backend: `docker-compose restart backend`
4. Check file permissions: `chmod 644 backend/fonts/*.ttf`

### Font download script fails

**Issue:** `./download_fonts.sh` fails with errors

**Solutions:**
1. Install wget: `apt-get install wget` or `brew install wget`
2. Install unzip: `apt-get install unzip`
3. Check internet connection
4. Try manual download from URLs in README.md
5. Use specific URLs from Google Fonts

### Font size too large/small

**Issue:** Text doesn't fit or is hard to read

**Solutions:**
1. Use recommended sizes from `fonts.json`
2. Adjust `font_size` parameter (20-72 range)
3. Different fonts render differently at same size
4. Test with multiple fonts to find best fit

### Memory issues with large fonts

**Issue:** Backend crashes or slows down

**Solutions:**
1. Use compressed/optimized font files
2. Avoid very large font files (>5MB)
3. Limit font collection to 10-15 fonts
4. Consider font subsetting for production

## API Summary

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/fonts` | GET | List all fonts with metadata | JSON with fonts array, summary, metadata |
| `/fonts/{name}` | GET | Download font file | TTF file (font/ttf) |
| `/start` | POST | Process video with font options | Task data with clips |
| `/start-with-progress` | POST | Async video processing | Task ID for SSE tracking |

**Font Options Schema:**
```typescript
interface FontOptions {
  font_family: string;  // Font name (e.g., "Montserrat-Bold")
  font_size: number;    // Size in pixels (20-72)
  font_color: string;   // Hex color (e.g., "#FFFFFF")
}
```

## Best Practices

### Font Selection

1. **Social Media Content:** TikTokSans-Regular, Poppins-Bold
2. **Professional Videos:** Montserrat-Bold, Inter-Bold
3. **Maximum Readability:** Open Sans-Bold, Roboto-Bold
4. **Bold Impact:** THEBOLDFONT-FREEVERSION

### Font Sizing

- **Captions:** 24-48px
- **Titles:** 40-72px
- **Subtitles:** 20-36px

### Font Colors

- **White (#FFFFFF):** Universal, works on most backgrounds
- **Black (#000000):** For light backgrounds
- **Yellow (#FFFF00):** High visibility, TikTok-style
- **Custom colors:** Match brand guidelines

### Performance

- Keep font collection under 20 fonts
- Use TTF format (not OTF or WOFF)
- Prefer fonts under 1MB file size
- Cache font validation results

## Testing

### Manual Testing

```bash
# 1. List fonts
curl http://localhost:8000/fonts | jq

# 2. Download font
curl http://localhost:8000/fonts/TikTokSans-Regular -o test.ttf
file test.ttf  # Should show "TrueType Font data"

# 3. Process video with custom font
curl -X POST http://localhost:8000/start \
  -H "Content-Type: application/json" \
  -d '{
    "source": {"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"},
    "font_options": {
      "font_family": "Montserrat-Bold",
      "font_size": 40,
      "font_color": "#FFFFFF"
    }
  }'
```

### Automated Testing

```python
import requests

# Test font API
response = requests.get('http://localhost:8000/fonts')
assert response.status_code == 200
fonts = response.json()['fonts']
assert len(fonts) >= 2  # At least 2 pre-installed fonts

# Test font file download
installed_fonts = [f for f in fonts if f['installed']]
if installed_fonts:
    font_name = installed_fonts[0]['name']
    response = requests.get(f'http://localhost:8000/fonts/{font_name}')
    assert response.status_code == 200
    assert response.headers['content-type'] == 'font/ttf'
```

## Migration Guide

If you're upgrading from an older version that used Proxima Nova:

### Update API Requests

**Before:**
```json
{
  "font_options": {
    "font_family": "ProximaNova-Regular"
  }
}
```

**After:**
```json
{
  "font_options": {
    "font_family": "Montserrat-Bold"
  }
}
```

### Automatic Fallback

Don't worry - the system will automatically fall back to available fonts if you specify a missing font. Your existing code will continue to work.

### Recommended Proxima Nova Alternatives

| Proxima Nova Variant | Recommended Alternative |
|---------------------|-------------------------|
| Proxima Nova Regular | Montserrat-Bold |
| Proxima Nova Bold | Montserrat-Bold |
| Proxima Nova Semibold | Inter-Bold |
| Proxima Nova Black | THEBOLDFONT-FREEVERSION |

## Support & Resources

- **Font Documentation:** `backend/fonts/README.md`
- **Font Manifest:** `backend/fonts/fonts.json`
- **Download Script:** `backend/fonts/download_fonts.sh`
- **API Docs:** http://localhost:8000/docs

## Changelog

### Version 1.0.0 (2025-11-10)

**Added:**
- Font metadata system (fonts.json)
- Enhanced GET /fonts API with rich metadata
- Font validation in VideoProcessor
- Font validation in CaptionGenerator
- Font validation in TitleCardGenerator
- Automated font downloader script
- Comprehensive font documentation
- 5 recommended open-source fonts
- Fallback system for missing fonts
- Recommended size application from metadata

**Changed:**
- Default font from Proxima Nova to TikTokSans-Regular
- Font paths now validated before use
- Better error handling and logging

**Fixed:**
- Hard-coded Proxima Nova references
- Missing font errors
- Font path resolution issues

---

**Last Updated:** 2025-11-10
**SupoClip Version:** 1.0.0
