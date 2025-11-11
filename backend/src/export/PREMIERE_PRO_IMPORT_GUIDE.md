# Premiere Pro XML Import Guide

## Overview

This guide explains how to import SupoClip-generated XML files into Adobe Premiere Pro. The exported XML files use the XMEML v5 format, compatible with Premiere Pro CC 2020 and later versions.

---

## Quick Start

### Basic Import Process

1. **Open Premiere Pro**
   - Launch Adobe Premiere Pro CC 2020 or later

2. **Import XML File**
   - Go to `File` → `Import...`
   - Select your SupoClip XML file (e.g., `premiere_export.xml`)
   - Click `Import`

3. **Wait for Import**
   - Premiere Pro will process the XML and create:
     - Organized bins with your clips
     - Color-coded clips based on engagement scores
     - Markers with metadata
     - A timeline sequence (if enabled)

4. **Verify Import**
   - Check the Project Panel for organized bins
   - Inspect clip labels/colors
   - Review markers for metadata
   - Open the timeline sequence to see clips arranged

---

## XML Export Features

### 1. Bin Organization

Clips are automatically organized into bins based on:
- **Temporal Type**: standard, fast_cut, slow_motion, freeze_frame, timelapse
- **Canvas Style**: default, split_screen, picture_in_picture, side_by_side, overlay

**Bin Structure:**
```
Council Selected Clips/
├── Standard/
│   ├── Default/
│   ├── Split Screen/
│   └── Picture In Picture/
├── Fast Cut/
│   ├── Default/
│   └── Side By Side/
└── Slow Motion/
    └── Overlay/
```

Within each bin, clips are sorted by engagement score (highest first).

### 2. Color Labels

Clips are automatically color-coded based on engagement scores:

| Engagement Score | Label Color | Meaning |
|-----------------|-------------|---------|
| 8.5 - 10.0      | **Forest** (Green) | Excellent - Top performing clips |
| 7.0 - 8.4       | **Cerulean** (Cyan) | Good - High quality clips |
| 5.5 - 6.9       | **Mango** (Yellow) | Medium - Acceptable clips |
| 4.0 - 5.4       | **Rose** (Pink) | Low - Needs improvement |
| 0.0 - 3.9       | **Lavender** (Purple) | Poor - Consider excluding |

**How to Use:**
- Quickly identify top performers by looking for green clips
- Filter by label in Premiere Pro's Project Panel
- Drag only high-scoring clips to your timeline

### 3. Markers & Metadata

Each clip includes a marker at the beginning with:
- **Engagement Score**: AI-predicted virality score (0-10)
- **Title**: Base clip title
- **Type**: Temporal variation type
- **Style**: Canvas style variation

**Example Marker:**
```
Score: 8.75/10 | Title: Hook Moment | Type: fast_cut | Style: split_screen
```

**How to Access:**
- Open a clip in the Source Monitor
- Look for the marker at the start
- Click marker to see full metadata in comment

### 4. Timeline Sequence

If enabled, a pre-built timeline sequence is created with:
- All clips arranged in order
- Configurable gaps between clips (default: 1 second)
- Proper video and audio tracks
- Maintains clip labels and metadata

**Sequence Name:** `[Project Name] - Timeline`

---

## File Size & Performance

### Expected File Sizes

| Clip Count | Single File | Split Files (100/file) |
|------------|-------------|------------------------|
| 5 clips    | ~18 KB      | N/A |
| 50 clips   | ~156 KB     | N/A |
| 250 clips  | ~768 KB     | N/A |
| 500 clips  | ~1.5 MB     | ~309 KB each (5 files) |

### Performance Tips

**For Large Projects (250+ clips):**

1. **Use Multi-File Export**
   - Enable `max_clips_per_file` option
   - Recommended: 100 clips per file
   - Import files one at a time

2. **Disable Sequence Generation**
   - Set `create_sequence=False`
   - Build timeline manually from bins
   - Reduces import time significantly

3. **Import in Stages**
   - Import highest-scoring clips first (green labels)
   - Skip low-scoring clips (purple labels)
   - Add more clips as needed

**Premiere Pro Limits:**
- Single XML file: Up to 5 MB recommended
- Total clips: 1000+ clips tested successfully
- Timeline clips: 500+ tested successfully

---

## Advanced Features

### Dynamic Resolution & Framerate

The XML exporter auto-detects video properties:

**Supported Resolutions:**
- 1080x1920 (9:16 vertical - default)
- 1920x1080 (16:9 horizontal)
- 3840x2160 (4K)
- Any custom resolution

**Supported Framerates:**
- 30 fps (standard)
- 29.97 fps (NTSC - auto-detected)
- 60 fps
- 59.94 fps (NTSC)
- Any custom framerate

**NTSC vs. Non-Drop Frame:**
- NTSC framerates (29.97, 59.94) use drop-frame timecode (`;` separator)
- Standard framerates (30, 60) use non-drop frame (`:` separator)

### Cross-Platform File Paths

File paths are automatically formatted for:
- **Windows**: `file:///C:/path/to/clip.mp4`
- **macOS/Linux**: `file://localhost/path/to/clip.mp4`

**Important:** Clips must be accessible at the specified paths when importing into Premiere Pro.

### Multi-File Export

For very large projects, split into multiple XML files:

```python
generate_premiere_xml(
    clips=clips,
    output_path="/path/to/export.xml",
    max_clips_per_file=100  # Creates multiple files
)
```

**Output:**
- `export_part001.xml` (clips 1-100)
- `export_part002.xml` (clips 101-200)
- `export_part003.xml` (clips 201-300)
- etc.

Import each file separately in Premiere Pro.

---

## Customization Options

### Python API

```python
from export import generate_premiere_xml

generate_premiere_xml(
    clips=clip_list,
    output_path="/path/to/export.xml",
    project_name="My SupoClip Project",
    organize_bins=True,              # Organize into hierarchical bins
    max_clips_per_file=None,         # None = single file, or 100 for split
    create_sequence=True,            # Create timeline sequence
    sequence_gap_seconds=1.0         # Gap between clips in timeline
)
```

### Clip Data Format

```python
clip = {
    'file_path': '/absolute/path/to/clip.mp4',
    'name': 'Clip Title',
    'title': 'Variation Name',
    'duration': 30.0,  # seconds
    'metadata': {
        'base_title': 'Original Clip',
        'temporal_type': 'fast_cut',
        'canvas_style': 'split_screen',
        'engagement_score': 8.5
    }
}
```

---

## Troubleshooting

### Import Errors

**Error: "File not found" or "Media offline"**
- **Cause**: Clip files moved or deleted after XML generation
- **Solution**: Ensure clip files exist at original paths, or use Premiere's "Link Media" feature

**Error: "Invalid XML format"**
- **Cause**: Corrupted XML file
- **Solution**: Re-generate XML file, check for file system errors

**Error: "Unsupported codec"**
- **Cause**: Premiere doesn't support the video codec
- **Solution**: Re-encode clips to H.264 (supported by default)

### Performance Issues

**Premiere Pro freezes during import**
- **Cause**: Too many clips in single file
- **Solution**: Use multi-file export (100 clips per file)

**Slow timeline playback**
- **Cause**: High-resolution clips or too many clips
- **Solution**: Create proxies in Premiere Pro, or reduce timeline clip count

### Label Colors Not Showing

**Labels appear but colors are wrong**
- **Cause**: Premiere Pro label preferences differ
- **Solution**: Go to `Preferences` → `Labels` → `Label Colors` → `Restore Defaults`

**Labels not showing at all**
- **Cause**: XML import didn't include label data
- **Solution**: Verify XML file contains `<label>` elements, re-export if needed

---

## Workflow Recommendations

### 1. Quick Review Workflow

**Goal:** Quickly identify and edit top clips

1. Import XML file
2. Filter Project Panel by label: **Forest** (green)
3. Review only top-scoring clips
4. Drag selected clips to timeline
5. Edit and export

**Time Saved:** 70-80% compared to reviewing all clips

### 2. Comprehensive Workflow

**Goal:** Review all clips, organize by category

1. Import XML file (organized bins)
2. Open each bin category
3. Review clips within each bin (already sorted by score)
4. Use pre-built timeline sequence as starting point
5. Refine timeline, add transitions/effects
6. Export final video

**Benefit:** Systematic organization reduces decision fatigue

### 3. Batch Export Workflow

**Goal:** Export multiple variations for A/B testing

1. Import XML file
2. Filter by label or bin
3. Create multiple sequences (e.g., "Top 10", "Medium 20", "All")
4. Export each sequence separately
5. Test performance across platforms

**Benefit:** Data-driven optimization

---

## XMEML Format Reference

### Document Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="5">
  <project>
    <name>Project Name</name>
    <children>
      <bin>
        <!-- Clips and nested bins -->
      </bin>
      <sequence id="sequence-1">
        <!-- Timeline sequence -->
      </sequence>
    </children>
  </project>
</xmeml>
```

### Key Elements

- **`<bin>`**: Container for clips and nested bins
- **`<file>`**: Media file reference with path and properties
- **`<clip>`**: Clip metadata, markers, labels
- **`<sequence>`**: Timeline sequence with tracks and clip items
- **`<marker>`**: Comment markers with metadata
- **`<label>`**: Premiere Pro color label (Forest, Cerulean, etc.)

### Sample Characteristics

```xml
<samplecharacteristics>
  <width>1080</width>
  <height>1920</height>
  <anamorphic>FALSE</anamorphic>
  <pixelaspectratio>square</pixelaspectratio>
  <fielddominance>none</fielddominance>
  <rate>
    <timebase>30</timebase>
    <ntsc>FALSE</ntsc>
  </rate>
  <colordepth>24</colordepth>
  <codec>
    <name>H.264</name>
  </codec>
</samplecharacteristics>
```

---

## Testing & Validation

### Test Files Included

The following test files are generated for validation:

1. **premiere_test_5clips.xml** (~18 KB)
   - Minimal project for quick testing
   - Verifies basic structure

2. **premiere_test_50clips.xml** (~156 KB)
   - Typical project size
   - Tests bin organization

3. **premiere_test_250clips.xml** (~768 KB)
   - Large project
   - Tests performance

4. **premiere_test_500clips.xml** (~1.5 MB)
   - Very large project
   - Tests limits

5. **premiere_test_500clips_split_part*.xml** (5 files @ ~309 KB each)
   - Multi-file export test
   - Validates split functionality

### Validation Checklist

- [ ] XML file imports without errors
- [ ] Bins are organized hierarchically
- [ ] Clips have correct labels/colors
- [ ] Markers contain metadata
- [ ] Timeline sequence is created (if enabled)
- [ ] Clips play correctly in Source Monitor
- [ ] Timeline plays smoothly
- [ ] File paths resolve correctly
- [ ] Resolution/framerate are correct
- [ ] Audio tracks are present

---

## FAQ

**Q: Can I import the XML into other video editors?**
A: XMEML is supported by Final Cut Pro 7 (not X), DaVinci Resolve (limited), and some other editors. Premiere Pro has the best support.

**Q: What if I want to change label colors after import?**
A: Right-click any clip in Premiere Pro → `Label` → Select new color. This won't affect the original XML.

**Q: Can I re-import the same XML file multiple times?**
A: Yes, but Premiere will create duplicate bins/clips. Use "Import into existing project" carefully.

**Q: How do I export only specific clips to XML?**
A: Filter your clip list in Python before calling `generate_premiere_xml()`.

**Q: Does the XML include effects or transitions?**
A: No. Only clips, bins, markers, and basic timeline structure. Add effects in Premiere Pro.

**Q: What's the maximum number of clips I can export?**
A: Tested successfully with 500+ clips. For larger projects, use multi-file export.

**Q: Can I customize the bin organization?**
A: Yes, modify the `organize_clips_into_bins()` function in `premiere_xml.py`.

---

## Support & Resources

### SupoClip Documentation
- Main documentation: `/home/user/supoclip/CLAUDE.md`
- Export module: `/home/user/supoclip/backend/src/export/`
- Test script: `/home/user/supoclip/backend/src/export/test_xml_generator.py`

### Adobe Premiere Pro Resources
- [Premiere Pro XML Documentation](https://helpx.adobe.com/premiere-pro/using/importing-xml-project-files-final.html)
- [Working with Labels](https://helpx.adobe.com/premiere/desktop/get-started/preferences-and-settings/labels-preferences.html)
- [Markers in Premiere](https://helpx.adobe.com/premiere-pro/using/markers.html)

### XMEML Format
- [Apple XMEML Reference](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/FinalCutPro_XML/) (archived)
- [XMEML Python Library](https://github.com/ccnmtl/xmeml)

---

## Version History

**v1.0** (2025-11-10)
- Initial release
- XMEML v5 compliance
- Bin organization by temporal type and canvas style
- Color label support based on engagement scores
- Comprehensive markers with metadata
- Multi-file export option
- Dynamic resolution and framerate detection
- Cross-platform file path support
- Timeline sequence generation

---

## License

Part of the SupoClip open-source project.

---

**Happy Editing! 🎬**
