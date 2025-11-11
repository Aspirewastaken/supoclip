"""
Premiere Pro XML (XMEML v4/v5) generator.

Exports clips in format compatible with Premiere Pro CC 2020+.
Supports bin organization, color labels, markers, and multi-file export.
"""
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict

logger = logging.getLogger(__name__)


# Premiere Pro label colors
LABEL_COLORS = {
    'violet': 'Lavender',
    'cyan': 'Cerulean',
    'green': 'Forest',
    'pink': 'Rose',
    'yellow': 'Mango',
    'blue': 'Iris',
    'red': 'Caribbean',
    'teal': 'Teal'
}


def get_label_for_score(score: float) -> str:
    """
    Get Premiere Pro label color based on engagement score.

    Args:
        score: Engagement score (0-10)

    Returns:
        Label color name
    """
    if score >= 8.5:
        return 'Forest'  # Green for excellent
    elif score >= 7.0:
        return 'Cerulean'  # Cyan for good
    elif score >= 5.5:
        return 'Mango'  # Yellow for medium
    elif score >= 4.0:
        return 'Rose'  # Pink for low
    else:
        return 'Lavender'  # Purple for poor


def detect_video_properties(file_path: str) -> Dict[str, Any]:
    """
    Detect video properties from file.

    Args:
        file_path: Path to video file

    Returns:
        Dict with width, height, fps, duration
    """
    try:
        from moviepy.editor import VideoFileClip
        with VideoFileClip(file_path) as video:
            return {
                'width': video.w,
                'height': video.h,
                'fps': video.fps,
                'duration': video.duration
            }
    except Exception as e:
        logger.warning(f"Could not detect properties for {file_path}: {e}")
        # Return defaults (9:16 vertical, 30fps)
        return {
            'width': 1080,
            'height': 1920,
            'fps': 30,
            'duration': 30.0
        }


def frames_to_timecode(frames: int, fps: float, drop_frame: bool = False) -> str:
    """
    Convert frames to SMPTE timecode string.

    Args:
        frames: Frame count
        fps: Frames per second
        drop_frame: Whether to use drop-frame notation

    Returns:
        Timecode string (HH:MM:SS:FF or HH:MM:SS;FF for drop-frame)
    """
    total_seconds = frames / fps
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    frame = int(frames % fps)

    separator = ';' if drop_frame else ':'
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{frame:02d}"


def organize_clips_into_bins(clips: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Organize clips into bins by temporal type and canvas style.

    Args:
        clips: List of clip dictionaries

    Returns:
        Dict mapping bin name to list of clips
    """
    bins = defaultdict(list)

    for clip in clips:
        metadata = clip.get('metadata', {})
        temporal = metadata.get('temporal_type', 'standard')
        canvas = metadata.get('canvas_style', 'default')

        # Create hierarchical bin structure
        bin_name = f"{temporal.title()} / {canvas.title()}"
        bins[bin_name].append(clip)

    # Sort clips within each bin by engagement score (highest first)
    for bin_name in bins:
        bins[bin_name].sort(
            key=lambda c: c.get('metadata', {}).get('engagement_score', 0),
            reverse=True
        )

    return bins


def create_file_element(
    file_id: str,
    file_path: str,
    duration_frames: int,
    fps: float,
    width: int,
    height: int,
    is_ntsc: bool = False
) -> ET.Element:
    """
    Create XMEML file element with proper structure.

    Args:
        file_id: Unique file identifier
        file_path: Absolute path to file
        duration_frames: Duration in frames
        fps: Frames per second
        width: Video width in pixels
        height: Video height in pixels
        is_ntsc: Whether NTSC framerate

    Returns:
        XML Element for file
    """
    file_elem = ET.Element('file', id=file_id)

    # Name and path
    ET.SubElement(file_elem, 'name').text = Path(file_path).name

    # Convert path to URL format (cross-platform)
    if os.name == 'nt':
        # Windows: file:///C:/path/to/file.mp4
        path_url = f"file:///{file_path.replace(os.sep, '/')}"
    else:
        # Unix: file://localhost/path/to/file.mp4
        path_url = f"file://localhost{file_path}"

    ET.SubElement(file_elem, 'pathurl').text = path_url

    # Rate
    rate = ET.SubElement(file_elem, 'rate')
    ET.SubElement(rate, 'timebase').text = str(int(fps))
    ET.SubElement(rate, 'ntsc').text = 'TRUE' if is_ntsc else 'FALSE'

    # Duration
    ET.SubElement(file_elem, 'duration').text = str(duration_frames)

    # Timecode
    timecode = ET.SubElement(file_elem, 'timecode')
    tc_rate = ET.SubElement(timecode, 'rate')
    ET.SubElement(tc_rate, 'timebase').text = str(int(fps))
    ET.SubElement(tc_rate, 'ntsc').text = 'TRUE' if is_ntsc else 'FALSE'
    ET.SubElement(timecode, 'string').text = frames_to_timecode(0, fps, is_ntsc)
    ET.SubElement(timecode, 'frame').text = '0'
    ET.SubElement(timecode, 'displayformat').text = 'DF' if is_ntsc else 'NDF'

    # Media
    media = ET.SubElement(file_elem, 'media')

    # Video
    video = ET.SubElement(media, 'video')
    video_char = ET.SubElement(video, 'samplecharacteristics')

    # Video characteristics
    ET.SubElement(video_char, 'width').text = str(width)
    ET.SubElement(video_char, 'height').text = str(height)
    ET.SubElement(video_char, 'anamorphic').text = 'FALSE'
    ET.SubElement(video_char, 'pixelaspectratio').text = 'square'
    ET.SubElement(video_char, 'fielddominance').text = 'none'

    # Rate in characteristics
    char_rate = ET.SubElement(video_char, 'rate')
    ET.SubElement(char_rate, 'timebase').text = str(int(fps))
    ET.SubElement(char_rate, 'ntsc').text = 'TRUE' if is_ntsc else 'FALSE'

    # Color depth
    ET.SubElement(video_char, 'colordepth').text = '24'

    # Codec (H.264)
    codec = ET.SubElement(video_char, 'codec')
    ET.SubElement(codec, 'name').text = 'H.264'
    ET.SubElement(codec, 'appspecificdata')

    # Audio
    audio = ET.SubElement(media, 'audio')
    audio_char = ET.SubElement(audio, 'samplecharacteristics')
    ET.SubElement(audio_char, 'depth').text = '16'
    ET.SubElement(audio_char, 'samplerate').text = '48000'

    # Audio channel layout
    channelcount = ET.SubElement(audio_char, 'channelcount')
    channelcount.text = '2'

    return file_elem


def create_clip_element(
    clip_id: str,
    clip_data: Dict[str, Any],
    file_id: str,
    duration_frames: int,
    fps: float,
    is_ntsc: bool = False
) -> ET.Element:
    """
    Create XMEML clip element with markers and metadata.

    Args:
        clip_id: Unique clip identifier
        clip_data: Clip data dictionary
        file_id: Reference to file element
        duration_frames: Duration in frames
        fps: Frames per second
        is_ntsc: Whether NTSC framerate

    Returns:
        XML Element for clip
    """
    clip_elem = ET.Element('clip', id=clip_id)

    # Name
    clip_name = clip_data.get('name', clip_data.get('title', 'Untitled'))
    ET.SubElement(clip_elem, 'name').text = clip_name

    # Duration
    ET.SubElement(clip_elem, 'duration').text = str(duration_frames)

    # Rate
    rate = ET.SubElement(clip_elem, 'rate')
    ET.SubElement(rate, 'timebase').text = str(int(fps))
    ET.SubElement(rate, 'ntsc').text = 'TRUE' if is_ntsc else 'FALSE'

    # In/Out points (full clip)
    ET.SubElement(clip_elem, 'in').text = '0'
    ET.SubElement(clip_elem, 'out').text = str(duration_frames)

    # File reference
    file_ref = ET.SubElement(clip_elem, 'file', id=file_id)

    # Label (color coding based on engagement score)
    metadata = clip_data.get('metadata', {})
    engagement_score = metadata.get('engagement_score', 0)
    label = get_label_for_score(engagement_score)
    ET.SubElement(clip_elem, 'label').text = label

    # Labels container (for backward compatibility)
    labels = ET.SubElement(clip_elem, 'labels')
    ET.SubElement(labels, 'label2').text = label

    # Markers with comprehensive metadata
    if metadata:
        markers = ET.SubElement(clip_elem, 'markers')
        marker = ET.SubElement(markers, 'marker')

        # Build marker comment with all metadata
        marker_text_parts = []

        if engagement_score:
            marker_text_parts.append(f"Score: {engagement_score:.2f}/10")

        if 'base_title' in metadata:
            marker_text_parts.append(f"Title: {metadata['base_title']}")

        if 'temporal_type' in metadata:
            marker_text_parts.append(f"Type: {metadata['temporal_type']}")

        if 'canvas_style' in metadata:
            marker_text_parts.append(f"Style: {metadata['canvas_style']}")

        marker_comment = " | ".join(marker_text_parts)
        ET.SubElement(marker, 'comment').text = marker_comment
        ET.SubElement(marker, 'name').text = 'SupoClip Metadata'
        ET.SubElement(marker, 'in').text = '0'
        ET.SubElement(marker, 'out').text = str(min(90, duration_frames))  # 3 seconds or full clip

    # Logging info
    if 'base_title' in metadata:
        logginginfo = ET.SubElement(clip_elem, 'logginginfo')
        ET.SubElement(logginginfo, 'description').text = metadata.get('base_title', '')
        if 'temporal_type' in metadata:
            ET.SubElement(logginginfo, 'scene').text = metadata['temporal_type']
        if 'canvas_style' in metadata:
            ET.SubElement(logginginfo, 'shottake').text = metadata['canvas_style']

    return clip_elem


def generate_premiere_xml(
    clips: List[Dict[str, Any]],
    output_path: str,
    project_name: str = "SupoClip Export",
    organize_bins: bool = True,
    max_clips_per_file: Optional[int] = None,
    create_sequence: bool = True,
    sequence_gap_seconds: float = 1.0
) -> str:
    """
    Generate Premiere Pro XML file from clips.

    Args:
        clips: List of clip dicts with file_path, duration, metadata, etc.
        output_path: Where to save the XML file
        project_name: Name for the Premiere project
        organize_bins: Whether to organize clips into bins by category
        max_clips_per_file: Split into multiple XML files (None = single file)
        create_sequence: Whether to create a timeline sequence
        sequence_gap_seconds: Gap between clips in sequence timeline (seconds)

    Returns:
        Path to generated XML file (or base path if multiple files)
    """
    logger.info(f"Generating Premiere XML for {len(clips)} clips")

    # Split into multiple files if needed
    if max_clips_per_file and len(clips) > max_clips_per_file:
        logger.info(f"Splitting into multiple XML files ({max_clips_per_file} clips per file)")

        output_dir = Path(output_path).parent
        output_base = Path(output_path).stem
        output_ext = Path(output_path).suffix

        generated_files = []
        for i in range(0, len(clips), max_clips_per_file):
            chunk = clips[i:i + max_clips_per_file]
            chunk_num = (i // max_clips_per_file) + 1
            chunk_path = output_dir / f"{output_base}_part{chunk_num:03d}{output_ext}"

            _generate_single_xml(
                clips=chunk,
                output_path=str(chunk_path),
                project_name=f"{project_name} - Part {chunk_num}",
                organize_bins=organize_bins,
                create_sequence=create_sequence,
                sequence_gap_seconds=sequence_gap_seconds
            )
            generated_files.append(str(chunk_path))

        logger.info(f"✅ Generated {len(generated_files)} XML files")
        return output_path  # Return base path

    # Single file
    return _generate_single_xml(
        clips=clips,
        output_path=output_path,
        project_name=project_name,
        organize_bins=organize_bins,
        create_sequence=create_sequence,
        sequence_gap_seconds=sequence_gap_seconds
    )


def _generate_single_xml(
    clips: List[Dict[str, Any]],
    output_path: str,
    project_name: str,
    organize_bins: bool,
    create_sequence: bool,
    sequence_gap_seconds: float
) -> str:
    """
    Generate a single Premiere Pro XML file.

    Internal function - use generate_premiere_xml() instead.
    """
    # Detect video properties from first clip
    if clips:
        first_clip_props = detect_video_properties(clips[0]['file_path'])
        default_fps = first_clip_props['fps']
        default_width = first_clip_props['width']
        default_height = first_clip_props['height']
    else:
        default_fps = 30
        default_width = 1080
        default_height = 1920

    # Determine if NTSC (29.97, 59.94, etc.)
    is_ntsc = abs(default_fps - round(default_fps)) > 0.01

    # Create root with DOCTYPE
    xmeml = ET.Element('xmeml', version="5")

    # Create project
    project = ET.SubElement(xmeml, 'project')
    ET.SubElement(project, 'name').text = project_name

    # Project children
    children = ET.SubElement(project, 'children')

    # Organize clips into bins or single bin
    if organize_bins and len(clips) > 0:
        bins_dict = organize_clips_into_bins(clips)
        logger.info(f"Organized into {len(bins_dict)} bins")
    else:
        bins_dict = {'All Clips': clips}

    # Track all file IDs for later reference
    file_id_map = {}
    clip_index = 0

    # Create bins and clips
    for bin_name, bin_clips in bins_dict.items():
        # Create bin
        bin_elem = ET.SubElement(children, 'bin')

        # Parse hierarchical bin names (e.g., "Temporal / Canvas")
        bin_parts = [part.strip() for part in bin_name.split('/')]
        ET.SubElement(bin_elem, 'name').text = bin_parts[0]

        # If hierarchical, create nested bins
        current_bin = bin_elem
        for bin_part in bin_parts[1:]:
            bin_children = ET.SubElement(current_bin, 'children')
            nested_bin = ET.SubElement(bin_children, 'bin')
            ET.SubElement(nested_bin, 'name').text = bin_part
            current_bin = nested_bin

        # Add clips to innermost bin
        bin_children = ET.SubElement(current_bin, 'children')

        for clip_data in bin_clips:
            clip_index += 1
            clip_id = f"clip-{clip_index}"
            file_id = f"file-{clip_index}"

            # Detect clip properties
            clip_props = detect_video_properties(clip_data['file_path'])
            clip_duration = clip_data.get('duration', clip_props['duration'])
            clip_fps = clip_props.get('fps', default_fps)
            clip_width = clip_props.get('width', default_width)
            clip_height = clip_props.get('height', default_height)
            duration_frames = int(clip_duration * clip_fps)

            # Create file element
            file_elem = create_file_element(
                file_id=file_id,
                file_path=clip_data['file_path'],
                duration_frames=duration_frames,
                fps=clip_fps,
                width=clip_width,
                height=clip_height,
                is_ntsc=is_ntsc
            )
            bin_children.append(file_elem)

            # Create clip element
            clip_elem = create_clip_element(
                clip_id=clip_id,
                clip_data=clip_data,
                file_id=file_id,
                duration_frames=duration_frames,
                fps=clip_fps,
                is_ntsc=is_ntsc
            )
            bin_children.append(clip_elem)

            # Store for sequence creation
            file_id_map[clip_index] = {
                'file_id': file_id,
                'clip_id': clip_id,
                'clip_data': clip_data,
                'duration_frames': duration_frames,
                'fps': clip_fps,
                'file_path': clip_data['file_path']
            }

    # Create sequence timeline (optional)
    if create_sequence and file_id_map:
        sequence = ET.SubElement(children, 'sequence', id="sequence-1")
        ET.SubElement(sequence, 'name').text = f'{project_name} - Timeline'
        ET.SubElement(sequence, 'duration').text = str(sum(c['duration_frames'] for c in file_id_map.values()))

        # Sequence rate
        seq_rate = ET.SubElement(sequence, 'rate')
        ET.SubElement(seq_rate, 'timebase').text = str(int(default_fps))
        ET.SubElement(seq_rate, 'ntsc').text = 'TRUE' if is_ntsc else 'FALSE'

        # Sequence timecode
        seq_timecode = ET.SubElement(sequence, 'timecode')
        tc_rate = ET.SubElement(seq_timecode, 'rate')
        ET.SubElement(tc_rate, 'timebase').text = str(int(default_fps))
        ET.SubElement(tc_rate, 'ntsc').text = 'TRUE' if is_ntsc else 'FALSE'
        ET.SubElement(seq_timecode, 'string').text = frames_to_timecode(0, default_fps, is_ntsc)
        ET.SubElement(seq_timecode, 'frame').text = '0'
        ET.SubElement(seq_timecode, 'displayformat').text = 'DF' if is_ntsc else 'NDF'

        # Media
        seq_media = ET.SubElement(sequence, 'media')

        # Video track
        seq_video = ET.SubElement(seq_media, 'video')

        # Format (sequence settings)
        seq_format = ET.SubElement(seq_video, 'format')
        seq_char = ET.SubElement(seq_format, 'samplecharacteristics')
        ET.SubElement(seq_char, 'width').text = str(default_width)
        ET.SubElement(seq_char, 'height').text = str(default_height)
        ET.SubElement(seq_char, 'anamorphic').text = 'FALSE'
        ET.SubElement(seq_char, 'pixelaspectratio').text = 'square'
        ET.SubElement(seq_char, 'fielddominance').text = 'none'
        format_rate = ET.SubElement(seq_char, 'rate')
        ET.SubElement(format_rate, 'timebase').text = str(int(default_fps))
        ET.SubElement(format_rate, 'ntsc').text = 'TRUE' if is_ntsc else 'FALSE'
        ET.SubElement(seq_char, 'colordepth').text = '24'

        # Video track
        seq_video_track = ET.SubElement(seq_video, 'track')

        # Add clips to timeline with gaps
        current_time = 0
        gap_frames = int(sequence_gap_seconds * default_fps)

        for idx in sorted(file_id_map.keys()):
            clip_info = file_id_map[idx]
            clip_item = ET.SubElement(seq_video_track, 'clipitem', id=f"clipitem-{idx}")

            # Basic properties
            clip_name = clip_info['clip_data'].get('name', clip_info['clip_data'].get('title', f"Clip {idx}"))
            ET.SubElement(clip_item, 'name').text = clip_name
            ET.SubElement(clip_item, 'start').text = str(current_time)
            ET.SubElement(clip_item, 'end').text = str(current_time + clip_info['duration_frames'])
            ET.SubElement(clip_item, 'in').text = '0'
            ET.SubElement(clip_item, 'out').text = str(clip_info['duration_frames'])

            # File reference
            clip_file = ET.SubElement(clip_item, 'file', id=clip_info['file_id'])

            # Label
            metadata = clip_info['clip_data'].get('metadata', {})
            engagement_score = metadata.get('engagement_score', 0)
            label = get_label_for_score(engagement_score)
            ET.SubElement(clip_item, 'label').text = label

            # Move to next position (with gap)
            current_time += clip_info['duration_frames'] + gap_frames

        # Audio track
        seq_audio = ET.SubElement(seq_media, 'audio')
        seq_audio_format = ET.SubElement(seq_audio, 'format')
        audio_char = ET.SubElement(seq_audio_format, 'samplecharacteristics')
        ET.SubElement(audio_char, 'depth').text = '16'
        ET.SubElement(audio_char, 'samplerate').text = '48000'

        # Stereo output
        seq_audio_outputs = ET.SubElement(seq_audio, 'outputs')
        for i in range(2):
            output_group = ET.SubElement(seq_audio_outputs, 'group')
            ET.SubElement(output_group, 'index').text = str(i + 1)
            ET.SubElement(output_group, 'numchannels').text = '1'
            ET.SubElement(output_group, 'downmix').text = '0'
            channel = ET.SubElement(output_group, 'channel')
            ET.SubElement(channel, 'index').text = str(i + 1)

        # Audio track
        seq_audio_track = ET.SubElement(seq_audio, 'track')

    # Convert to pretty XML with DOCTYPE
    xml_str = ET.tostring(xmeml, encoding='utf-8')
    dom = minidom.parseString(xml_str)

    # Add DOCTYPE declaration
    doctype = '<!DOCTYPE xmeml>'
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
    pretty_xml = dom.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')

    # Insert DOCTYPE after XML declaration
    lines = pretty_xml.split('\n')
    if lines[0].startswith('<?xml'):
        lines.insert(1, doctype)
    else:
        lines.insert(0, xml_declaration)
        lines.insert(1, doctype)

    final_xml = '\n'.join(lines)

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_xml)

    logger.info(f"✅ Premiere XML generated: {output_path} ({len(clips)} clips)")

    return output_path
