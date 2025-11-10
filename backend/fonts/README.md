# SupoClip Font Library

This directory contains font files used for video captions and title cards. SupoClip currently ships with 2 fonts and recommends 5 additional high-quality open-source fonts.

## Pre-installed Fonts

### 1. **THEBOLDFONT-FREEVERSION** (Default Fallback)
- **File**: `THEBOLDFONT-FREEVERSION.ttf`
- **Style**: Bold Display Font
- **License**: Free for personal and commercial use
- **Best for**: Attention-grabbing captions, bold titles
- **Recommended size**: 48px

### 2. **TikTok Sans** (Default)
- **File**: `TikTokSans-Regular.ttf`
- **Style**: Sans-serif, modern
- **License**: TikTok proprietary (use with caution for commercial projects)
- **Best for**: Social media captions, recognizable TikTok style
- **Recommended size**: 32px

---

## Recommended Open-Source Fonts

These fonts are excellent **free alternatives to Proxima Nova** and other premium fonts. They're all licensed for commercial use.

### 1. **Montserrat Bold** ⭐ RECOMMENDED
**Best alternative to Proxima Nova**

- **Family**: Montserrat
- **Style**: Geometric sans-serif
- **License**: SIL Open Font License (free for commercial use)
- **Why use it**: Modern, clean, and very similar to Proxima Nova's geometric style
- **Best for**: Captions, titles, social media content

**Download Instructions:**
```bash
# Option 1: Download directly from Google Fonts
wget https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf -O backend/fonts/Montserrat-Bold.ttf

# Option 2: Using Google Fonts API
# Visit: https://fonts.google.com/specimen/Montserrat
# Click "Download family" and extract Montserrat-Bold.ttf
```

### 2. **Inter Bold**
**Best for UI and readability**

- **Family**: Inter
- **Style**: Sans-serif optimized for screens
- **License**: SIL Open Font License
- **Why use it**: Exceptional readability at all sizes, designed for digital screens
- **Best for**: Captions, subtitles, UI elements

**Download Instructions:**
```bash
# Download from Google Fonts
wget https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Bold.ttf -O backend/fonts/Inter-Bold.ttf

# Or visit: https://fonts.google.com/specimen/Inter
```

### 3. **Poppins Bold**
**Best for friendly, approachable content**

- **Family**: Poppins
- **Style**: Geometric sans-serif with rounded features
- **License**: SIL Open Font License
- **Why use it**: Friendly appearance, great for engaging social media content
- **Best for**: Social media captions, titles, lifestyle content

**Download Instructions:**
```bash
# Download from Google Fonts
wget https://github.com/itfoundry/Poppins/raw/master/products/Poppins-Bold.ttf -O backend/fonts/Poppins-Bold.ttf

# Or visit: https://fonts.google.com/specimen/Poppins
```

### 4. **Roboto Bold**
**Best for universal compatibility**

- **Family**: Roboto
- **Style**: Neo-grotesque sans-serif
- **License**: Apache License 2.0
- **Why use it**: Google's signature font, extremely versatile and recognizable
- **Best for**: All-purpose captions, subtitles, UI

**Download Instructions:**
```bash
# Download from Google Fonts
wget https://github.com/google/roboto/releases/download/v2.138/roboto-unhinted.zip
unzip roboto-unhinted.zip "Roboto-Bold.ttf" -d backend/fonts/

# Or visit: https://fonts.google.com/specimen/Roboto
```

### 5. **Open Sans Bold**
**Best for maximum legibility**

- **Family**: Open Sans
- **Style**: Humanist sans-serif
- **License**: SIL Open Font License
- **Why use it**: Highly legible, safe choice for all content types
- **Best for**: Subtitles, educational content, captions

**Download Instructions:**
```bash
# Download from Google Fonts
wget https://github.com/googlefonts/opensans/raw/main/fonts/ttf/OpenSans-Bold.ttf -O backend/fonts/OpenSans-Bold.ttf

# Or visit: https://fonts.google.com/specimen/Open+Sans
```

---

## Quick Setup: Download All Recommended Fonts

Run this script to download all recommended fonts at once:

```bash
#!/bin/bash
# File: backend/fonts/download_fonts.sh

cd "$(dirname "$0")"

echo "📥 Downloading recommended fonts..."

# Montserrat Bold
echo "Downloading Montserrat Bold..."
wget -q https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf -O Montserrat-Bold.ttf

# Inter Bold
echo "Downloading Inter Bold..."
wget -q https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Bold.ttf -O Inter-Bold.ttf

# Poppins Bold
echo "Downloading Poppins Bold..."
wget -q https://github.com/itfoundry/Poppins/raw/master/products/Poppins-Bold.ttf -O Poppins-Bold.ttf

# Roboto Bold
echo "Downloading Roboto Bold..."
wget -q https://github.com/google/roboto/releases/download/v2.138/roboto-unhinted.zip -O roboto-temp.zip
unzip -q -o roboto-temp.zip "Roboto-Bold.ttf"
rm roboto-temp.zip

# Open Sans Bold
echo "Downloading Open Sans Bold..."
wget -q https://github.com/googlefonts/opensans/raw/main/fonts/ttf/OpenSans-Bold.ttf -O OpenSans-Bold.ttf

echo "✅ All fonts downloaded successfully!"
echo "📋 Available fonts:"
ls -1 *.ttf
```

**Usage:**
```bash
chmod +x backend/fonts/download_fonts.sh
./backend/fonts/download_fonts.sh
```

---

## Font File Naming Convention

Font files must follow this naming pattern:
- **Filename**: `{FontFamily}-{Weight}.ttf` (e.g., `Montserrat-Bold.ttf`)
- **API Reference**: Use the filename without extension (e.g., `Montserrat-Bold`)

**Examples:**
```json
{
  "font_options": {
    "font_family": "Montserrat-Bold",
    "font_size": 40,
    "font_color": "#FFFFFF"
  }
}
```

---

## Adding Custom Fonts

To add your own custom fonts:

1. **Add the font file** to this directory (`backend/fonts/`)
   - Format: `.ttf` (TrueType Font)
   - Name it clearly: `MyFont-Bold.ttf`

2. **Update fonts.json** (optional, for metadata):
   ```json
   {
     "id": "myfont-bold",
     "name": "MyFont-Bold",
     "display_name": "My Font Bold",
     "family": "My Font",
     "file": "MyFont-Bold.ttf",
     "installed": true
   }
   ```

3. **Restart the backend** to make it available via API

4. **Use it in requests**:
   ```bash
   curl -X POST http://localhost:8000/start \
     -H "Content-Type: application/json" \
     -d '{
       "source": {"url": "https://youtube.com/watch?v=..."},
       "font_options": {
         "font_family": "MyFont-Bold",
         "font_size": 42,
         "font_color": "#FFFFFF"
       }
     }'
   ```

---

## Font Licensing

**Important**: Always verify font licenses before commercial use.

- ✅ **SIL Open Font License**: Free for personal and commercial use, including embedding in products
- ✅ **Apache License 2.0**: Free for personal and commercial use
- ⚠️ **TikTok Sans**: Proprietary license, use caution for commercial projects
- ❌ **Proxima Nova**: Commercial license required, not included in SupoClip

For hosted/commercial deployments, we recommend:
1. **Montserrat** (best Proxima Nova alternative)
2. **Inter** (best for readability)
3. **Poppins** (best for social media)

---

## Proxima Nova Alternative Comparison

| Feature | Proxima Nova | Montserrat | Inter | Poppins |
|---------|--------------|------------|-------|---------|
| **License** | ❌ Paid | ✅ Free | ✅ Free | ✅ Free |
| **Style** | Geometric sans | Geometric sans | Humanist sans | Geometric sans |
| **Readability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Social Media** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Modern Look** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Best Alternative** | - | ✅ | ✅ | ✅ |

**Recommendation**: Use **Montserrat Bold** as your primary Proxima Nova alternative. It's the closest match in style and works beautifully for social media content.

---

## API Usage

### List Available Fonts
```bash
GET http://localhost:8000/fonts
```

**Response:**
```json
{
  "fonts": [
    {
      "name": "Montserrat-Bold",
      "display_name": "Montserrat Bold",
      "category": "sans-serif",
      "installed": true,
      "recommended_size": {"min": 24, "max": 64, "default": 40}
    }
  ]
}
```

### Download Font File
```bash
GET http://localhost:8000/fonts/Montserrat-Bold
```

Returns the `.ttf` file for client-side preview/usage.

---

## Troubleshooting

### Font not found error
**Error**: `Font file not found: /app/fonts/MyFont.ttf`

**Solutions:**
1. Check the font file exists: `ls backend/fonts/MyFont.ttf`
2. Verify the filename matches (case-sensitive): `MyFont-Bold.ttf` ≠ `myfont-bold.ttf`
3. Restart the backend: `docker-compose restart backend`

### Font renders incorrectly
**Issue**: Font appears broken or missing characters

**Solutions:**
1. Verify it's a valid TrueType Font (`.ttf` format)
2. Test the font on your system first
3. Check font file isn't corrupted: `file MyFont.ttf` should show "TrueType Font data"
4. Some display fonts may not include all characters - use standard Unicode fonts for subtitles

### Font too large/small
**Issue**: Text doesn't fit or is hard to read

**Solutions:**
1. Adjust `font_size` in your request (recommended range: 20-72px)
2. Use fonts with recommended sizes from `fonts.json`
3. Test different fonts - some render larger/smaller at the same size

---

## Font Support

For issues, questions, or font recommendations:
- Open an issue on GitHub
- Check the documentation at [supoclip.com/docs](https://supoclip.com/docs)
- Community Discord: [discord.gg/supoclip](https://discord.gg/supoclip)

---

**Last Updated**: 2025-11-10
**SupoClip Version**: 1.0.0
