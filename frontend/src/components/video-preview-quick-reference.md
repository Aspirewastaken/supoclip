# Video Preview Component - Quick Reference

## Basic Import

```tsx
import { VideoPreview } from "@/components/video-preview"
```

## Minimal Example

```tsx
<VideoPreview
  sources={{
    id: "clip-1",
    url: "http://localhost:8000/clips/example.mp4"
  }}
/>
```

## Common Use Cases

### 1. Simple Video Player
```tsx
<VideoPreview sources={{ id: "1", url: videoUrl }} />
```

### 2. With Trimming Enabled
```tsx
<VideoPreview
  sources={{ id: "1", url: videoUrl }}
  enableTrimming={true}
  onTrimChange={(start, end) => console.log(start, end)}
/>
```

### 3. Show Frame Numbers
```tsx
<VideoPreview
  sources={{ id: "1", url: videoUrl }}
  showFrameNumber={true}
  fps={30}
/>
```

### 4. Compare Two Videos
```tsx
<VideoPreview
  sources={[
    { id: "1", url: url1, label: "Original" },
    { id: "2", url: url2, label: "Edited" }
  ]}
  comparisonMode={true}
/>
```

### 5. Full Featured
```tsx
<VideoPreview
  sources={{ id: "1", url: videoUrl }}
  enableTrimming={true}
  showFrameNumber={true}
  trimRange={[5, 15]}
  onTrimChange={(start, end) => saveTrim(start, end)}
  onTimeUpdate={(time) => console.log(time)}
  thumbnailInterval={1}
  fps={30}
/>
```

## Props Quick Reference

| Prop | Type | Default | Required |
|------|------|---------|----------|
| sources | VideoSource or VideoSource[] | - | Yes |
| enableTrimming | boolean | false | No |
| trimRange | [number, number] | undefined | No |
| onTrimChange | function | undefined | No |
| comparisonMode | boolean | false | No |
| showFrameNumber | boolean | false | No |
| fps | number | 30 | No |
| thumbnailInterval | number | 1 | No |
| autoPlay | boolean | false | No |
| onTimeUpdate | function | undefined | No |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| ← → | Skip 5s |
| , . | Frame step |
| M | Mute |
| F | Fullscreen |

## Demo

Visit: `http://localhost:3000/demo/video-preview`

## Documentation

See: `/home/user/supoclip/frontend/src/components/VIDEO_PREVIEW_README.md`
