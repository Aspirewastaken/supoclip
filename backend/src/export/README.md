# SupoClip Export Module

Export utilities for Premiere Pro and other video editing software.

## Overview

This module provides functionality to export SupoClip-generated clips into formats compatible with professional video editing software, starting with Adobe Premiere Pro (XMEML v5).

## Files

### Core Modules

- **`premiere_xml.py`** - Premiere Pro XML (XMEML v5) generator
- **`__init__.py`** - Module exports

### Documentation

- **`PREMIERE_PRO_IMPORT_GUIDE.md`** - Complete guide for importing XML into Premiere Pro
- **`VALIDATION_SUMMARY.md`** - Technical validation report and test results
- **`README.md`** - This file

### Testing

- **`test_xml_generator.py`** - Test suite for XML generation

### Test Output

Test XML files are generated in `/tmp/`:
- `premiere_test_5clips.xml` - Small project (19 KB)
- `premiere_test_50clips.xml` - Medium project (156 KB)
- `premiere_test_250clips.xml` - Large project (769 KB)
- `premiere_test_500clips.xml` - Very large project (1.5 MB)
- `premiere_test_500clips_split_part*.xml` - Multi-file export (5 files @ 309 KB each)

## Quick Start

### Basic Usage

```python
from export import generate_premiere_xml

# Prepare clip data
clips = [
    {
        'file_path': '/absolute/path/to/clip1.mp4',
        'name': 'Clip 1',
        'duration': 30.0,
        'metadata': {
            'base_title': 'Original Clip',
            'temporal_type': 'fast_cut',
            'canvas_style': 'split_screen',
            'engagement_score': 8.5
        }
    },
    # ... more clips
]

# Generate XML
xml_path = generate_premiere_xml(
    clips=clips,
    output_path="/path/to/export.xml",
    project_name="My SupoClip Project"
)

print(f"XML generated: {xml_path}")
```

### Advanced Usage

```python
# Large project with multi-file export
generate_premiere_xml(
    clips=clips,
    output_path="/path/to/export.xml",
    project_name="Large Project",
    organize_bins=True,           # Organize clips into bins
    max_clips_per_file=100,       # Split into multiple files
    create_sequence=True,         # Create timeline sequence
    sequence_gap_seconds=0.5      # Gap between clips
)
```

## Features

### XMEML v5 Compliance
- Full compliance with Final Cut Pro XML Interchange Format v5
- Compatible with Premiere Pro CC 2020+
- Proper DOCTYPE declaration and structure
- All required elements included

### Intelligent Organization
- **Hierarchical Bins** - Organized by temporal type and canvas style
- **Color Labels** - Automatic color coding based on engagement scores
- **Sorted by Quality** - Clips within bins sorted by score (highest first)

### Comprehensive Metadata
- **Markers** - Each clip has a marker with full metadata
- **Logging Info** - Description, scene, shot/take fields
- **Comments** - Engagement scores and variation details

### Scalability
- **Small Projects** - 5-50 clips in single file
- **Medium Projects** - 51-250 clips in single file
- **Large Projects** - 251+ clips with multi-file export option
- **Tested** - Up to 500 clips successfully validated

### Dynamic Detection
- **Resolution** - Auto-detects from video files (1080p, 4K, 9:16, etc.)
- **Framerate** - Auto-detects (30fps, 29.97, 60fps, 59.94, etc.)
- **NTSC Support** - Drop-frame timecode for NTSC framerates
- **Cross-Platform** - File paths formatted for Windows/macOS/Linux

### Timeline Generation
- **Optional Sequence** - Pre-built timeline with all clips
- **Configurable Gaps** - Set gap duration between clips
- **Proper Tracks** - Video and audio tracks configured
- **Label Preservation** - Clips retain color labels in timeline

## Color Label System

Clips are automatically color-coded based on engagement scores:

| Score Range | Color | Premiere Label | Meaning |
|-------------|-------|----------------|---------|
| 8.5 - 10.0  | Green | Forest | Excellent |
| 7.0 - 8.4   | Cyan | Cerulean | Good |
| 5.5 - 6.9   | Yellow | Mango | Medium |
| 4.0 - 5.4   | Pink | Rose | Low |
| 0.0 - 3.9   | Purple | Lavender | Poor |

## API Reference

### `generate_premiere_xml()`

```python
def generate_premiere_xml(
    clips: List[Dict[str, Any]],
    output_path: str,
    project_name: str = "SupoClip Export",
    organize_bins: bool = True,
    max_clips_per_file: Optional[int] = None,
    create_sequence: bool = True,
    sequence_gap_seconds: float = 1.0
) -> str
```

**Parameters:**
- `clips` - List of clip dictionaries (see format below)
- `output_path` - Where to save XML file
- `project_name` - Name for Premiere project
- `organize_bins` - Whether to organize clips into hierarchical bins
- `max_clips_per_file` - Split into multiple files (None = single file)
- `create_sequence` - Whether to create timeline sequence
- `sequence_gap_seconds` - Gap between clips in timeline (seconds)

**Returns:**
- Path to generated XML file (or base path if multi-file)

**Clip Data Format:**
```python
{
    'file_path': '/absolute/path/to/clip.mp4',  # Required
    'name': 'Clip Name',                         # Optional (defaults to 'Untitled')
    'title': 'Variation Title',                  # Optional
    'duration': 30.0,                            # Optional (auto-detected from file)
    'start': 0.0,                                # Optional (for reference)
    'metadata': {                                # Optional
        'base_title': 'Original Clip Title',
        'temporal_type': 'fast_cut',
        'canvas_style': 'split_screen',
        'engagement_score': 8.5
    }
}
```

## Testing

### Run Test Suite

```bash
cd /home/user/supoclip/backend
python src/export/test_xml_generator.py
```

**Test Cases:**
1. Small project (5 clips)
2. Medium project (50 clips)
3. Large project (250 clips)
4. Very large project (500 clips)
5. Multi-file split (500 clips → 5 files)
6. Different framerates
7. Different resolutions

**Expected Output:**
- 9 XML files in `/tmp/`
- File size analysis
- XML structure preview
- Performance metrics

## Documentation

### For Users

See **`PREMIERE_PRO_IMPORT_GUIDE.md`** for:
- How to import XML into Premiere Pro
- Feature explanations
- Troubleshooting
- Workflow recommendations
- FAQ

### For Developers

See **`VALIDATION_SUMMARY.md`** for:
- Technical specifications
- XMEML compliance details
- Test results
- Performance benchmarks
- Integration with SupoClip matrix system

## Integration

### SupoClip Matrix Worker

The export is integrated into the full matrix generation workflow:

**Location:** `/home/user/supoclip/backend/src/workers/full_matrix_task.py`

**Usage:**
```python
# After matrix processing completes
from ..export import generate_premiere_xml

xml_path = os.path.join(output_dir, "premiere_export.xml")

xml_clips = [
    {
        'file_path': var['file_path'],
        'name': var['filename'],
        'duration': var['duration'],
        'metadata': {
            'base_title': var['base_title'],
            'temporal_type': var['temporal_type'],
            'canvas_style': var['canvas_style'],
            'engagement_score': var['engagement_score']
        }
    }
    for var in manifest['variations']
]

generate_premiere_xml(
    clips=xml_clips,
    output_path=xml_path,
    project_name=f"SupoClip_{task_id}"
)
```

## File Size Guidelines

| Clip Count | Single File Size | Multi-File (100/file) | Recommendation |
|-----------|------------------|----------------------|----------------|
| 1-50      | ~20-160 KB       | N/A                  | Single file |
| 51-100    | ~160-320 KB      | N/A                  | Single file |
| 101-250   | ~320-800 KB      | 2-3 files @ ~310 KB  | Single or split |
| 251-500   | ~800-1600 KB     | 3-5 files @ ~310 KB  | Multi-file |
| 500+      | >1.6 MB          | 5+ files @ ~310 KB   | Multi-file |

**Premiere Pro Performance:**
- Files under 1 MB: Excellent
- Files 1-5 MB: Good
- Files over 5 MB: Consider splitting

## Troubleshooting

### Common Issues

**Issue:** "Could not detect properties for /path/to/clip.mp4: No module named 'moviepy'"
- **Cause:** MoviePy not installed or video file doesn't exist
- **Solution:** Falls back to defaults (1080x1920, 30fps). Harmless warning.

**Issue:** XML file is very large (>10 MB)
- **Cause:** Too many clips in single file
- **Solution:** Use `max_clips_per_file=100` to split into multiple files

**Issue:** Premiere Pro shows "File not found" errors
- **Cause:** Clip files moved or deleted after XML generation
- **Solution:** Ensure clip files exist at original paths, or use Premiere's "Link Media"

**Issue:** Labels/colors not showing in Premiere
- **Cause:** Premiere Pro label preferences differ
- **Solution:** Go to Preferences → Labels → Restore Defaults

## Future Enhancements

Potential future additions:

- [ ] Proxy file references
- [ ] Multi-track timeline support
- [ ] Nested sequence generation
- [ ] Transition templates
- [ ] Effect presets
- [ ] Export to DaVinci Resolve format
- [ ] Export to Final Cut Pro X format (FCPXML)
- [ ] Validation tool for XML files

## Contributing

When modifying this module:

1. Maintain XMEML v5 compliance
2. Update test suite for new features
3. Update documentation
4. Test with real Premiere Pro import
5. Verify file sizes remain reasonable

## License

Part of the SupoClip open-source project.

---

## Quick Reference

### File Locations

```
backend/src/export/
├── premiere_xml.py                    # Main XML generator
├── __init__.py                        # Module exports
├── test_xml_generator.py              # Test suite
├── PREMIERE_PRO_IMPORT_GUIDE.md       # User guide
├── VALIDATION_SUMMARY.md              # Technical validation
└── README.md                          # This file

/tmp/
├── premiere_test_5clips.xml           # Test: 5 clips
├── premiere_test_50clips.xml          # Test: 50 clips
├── premiere_test_250clips.xml         # Test: 250 clips
├── premiere_test_500clips.xml         # Test: 500 clips
└── premiere_test_500clips_split_*.xml # Test: Multi-file (5 files)
```

### Commands

```bash
# Run tests
python src/export/test_xml_generator.py

# Generate XML in Python
from export import generate_premiere_xml
generate_premiere_xml(clips, "/path/to/output.xml")

# Import in Premiere Pro
File → Import → Select XML file
```

---

**Status:** Production Ready ✅

Last Updated: 2025-11-10
