# SwipeControls Component

A powerful, fully-featured swipe navigation component built with React, TypeScript, and Framer Motion. Perfect for reviewing video clips with smooth animations and multiple interaction methods.

## Features

✅ **Left/Right Arrow Buttons** - Click navigation with visual feedback
✅ **Swipe Gesture Support** - Touch and mouse drag gestures
✅ **Keyboard Shortcuts** - Arrow keys, F (favorite), Delete (reject)
✅ **Smooth Animations** - Spring-based transitions using Framer Motion
✅ **Clip Counter Display** - Current position indicator
✅ **Quick Actions** - Optional favorite/reject buttons
✅ **Progress Dots** - Visual indicators with click-to-jump navigation
✅ **Responsive Design** - Works on mobile and desktop
✅ **Accessibility** - Full keyboard support and ARIA labels

## Installation

The component requires `framer-motion` which has been installed:

```bash
npm install framer-motion
```

## Basic Usage

```tsx
import { useState } from "react";
import SwipeControls from "@/components/swipe-controls";

const clips = [
  { id: "1", url: "http://localhost:8000/clips/clip1.mp4", title: "Clip 1" },
  { id: "2", url: "http://localhost:8000/clips/clip2.mp4", title: "Clip 2" },
  { id: "3", url: "http://localhost:8000/clips/clip3.mp4", title: "Clip 3" },
];

function ClipReview() {
  const [currentIndex, setCurrentIndex] = useState(0);

  return (
    <SwipeControls
      clips={clips}
      currentIndex={currentIndex}
      onNavigate={setCurrentIndex}
      renderContent={(clip) => (
        <video src={clip.url} controls autoPlay loop className="w-full" />
      )}
    />
  );
}
```

## Advanced Usage

```tsx
import SwipeControls from "@/components/swipe-controls";
import DynamicVideoPlayer from "@/components/dynamic-video-player";
import { toast } from "sonner";

function AdvancedClipReview() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());

  const handleFavorite = (clip) => {
    const newFavorites = new Set(favorites);
    if (newFavorites.has(clip.id)) {
      newFavorites.delete(clip.id);
      toast.info("Removed from favorites");
    } else {
      newFavorites.add(clip.id);
      toast.success("Added to favorites!");
    }
    setFavorites(newFavorites);
  };

  const handleReject = (clip) => {
    toast.error(`Rejected clip: ${clip.title}`);
    // Move to next clip after rejection
    if (currentIndex < clips.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  return (
    <SwipeControls
      clips={clips}
      currentIndex={currentIndex}
      onNavigate={setCurrentIndex}
      onFavorite={handleFavorite}
      onReject={handleReject}
      renderContent={(clip) => (
        <div className="space-y-4">
          <DynamicVideoPlayer
            src={clip.url}
            autoPlay
            muted
            loop
            className="mx-auto"
          />
          <h3 className="text-center font-semibold">{clip.title}</h3>
        </div>
      )}
      showQuickActions={true}
      swipeThreshold={50}
      animationDuration={0.3}
    />
  );
}
```

## Props

### Required Props

| Prop | Type | Description |
|------|------|-------------|
| `clips` | `Clip[]` | Array of clip objects (must have `id` and `url`) |
| `currentIndex` | `number` | Current clip index (0-based) |
| `onNavigate` | `(newIndex: number) => void` | Called when navigating to a new clip |
| `renderContent` | `(clip: Clip, index: number) => ReactNode` | Function to render clip content |

### Optional Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `onFavorite` | `(clip: Clip) => void` | `undefined` | Called when favoriting a clip |
| `onReject` | `(clip: Clip) => void` | `undefined` | Called when rejecting a clip |
| `className` | `string` | `""` | Additional CSS classes |
| `showQuickActions` | `boolean` | `true` | Show favorite/reject buttons |
| `swipeThreshold` | `number` | `50` | Pixels to trigger navigation |
| `animationDuration` | `number` | `0.3` | Animation duration in seconds |

### Clip Type

```typescript
interface Clip {
  id: string;
  url: string;
  [key: string]: any; // Additional properties like title, duration, etc.
}
```

## Keyboard Shortcuts

- **← Left Arrow**: Navigate to previous clip
- **→ Right Arrow**: Navigate to next clip
- **F**: Favorite current clip (when `onFavorite` is provided)
- **Delete/Backspace**: Reject current clip (when `onReject` is provided)

> Shortcuts are disabled when typing in input fields or textareas.

## Gesture Controls

### Touch Gestures
- **Swipe Left**: Next clip
- **Swipe Right**: Previous clip

### Mouse Gestures
- **Click & Drag Left**: Next clip
- **Click & Drag Right**: Previous clip

## UI Elements

### Counter Display
- Shows current position (e.g., "2 / 5")
- Fixed at top-center with backdrop blur
- Always visible

### Navigation Arrows
- Large circular buttons on left/right edges
- Automatically hide when at start/end
- Smooth transitions and hover effects

### Quick Action Buttons
- **Heart Icon**: Favorite action
- **X Icon**: Reject action
- Fixed at top-right corner
- Only shown when handlers are provided

### Progress Dots
- One dot per clip at bottom-center
- Active dot expands to show current position
- Click any dot to jump to that clip

### Swipe Hint
- Shows on first clip: "Swipe or use arrow keys"
- Automatically fades out after 2 seconds
- Only appears when multiple clips exist

## Animation Details

### Slide Transitions
- **Spring Physics**: Natural, responsive animations
- **Direction-Aware**: Slides left/right based on navigation
- **Opacity Fade**: Smooth fade in/out during transitions

### Configuration
```typescript
// Default animation settings
transition={{
  x: { type: "spring", stiffness: 300, damping: 30 },
  opacity: { duration: 0.3 },
}}
```

Customize via `animationDuration` prop.

## Integration with Video Player

### Using DynamicVideoPlayer

```tsx
import DynamicVideoPlayer from "@/components/dynamic-video-player";

<SwipeControls
  clips={clips}
  currentIndex={currentIndex}
  onNavigate={setCurrentIndex}
  renderContent={(clip) => (
    <DynamicVideoPlayer
      src={clip.url}
      autoPlay={true}
      muted={true}
      loop={true}
      className="mx-auto"
    />
  )}
/>
```

### Using HTML5 Video

```tsx
<SwipeControls
  clips={clips}
  currentIndex={currentIndex}
  onNavigate={setCurrentIndex}
  renderContent={(clip) => (
    <video
      src={clip.url}
      controls
      autoPlay
      muted
      loop
      className="w-full max-h-[70vh] mx-auto"
    />
  )}
/>
```

## Integration with Backend API

### Fetching Clips from SupoClip Backend

```tsx
import { useEffect, useState } from "react";

function ClipReviewPage({ taskId }: { taskId: string }) {
  const [clips, setClips] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchClips() {
      try {
        const response = await fetch(`http://localhost:8000/tasks/${taskId}/clips`);
        const data = await response.json();

        // Transform backend clips to component format
        const formattedClips = data.map((clip) => ({
          id: clip.id,
          url: `http://localhost:8000/clips/${clip.filename}`,
          title: clip.segment_text?.substring(0, 50) + "...",
          duration: clip.duration,
          startTime: clip.start_time,
          endTime: clip.end_time,
        }));

        setClips(formattedClips);
        setLoading(false);
      } catch (error) {
        console.error("Failed to fetch clips:", error);
        setLoading(false);
      }
    }

    fetchClips();
  }, [taskId]);

  if (loading) return <div>Loading clips...</div>;

  return (
    <SwipeControls
      clips={clips}
      currentIndex={currentIndex}
      onNavigate={setCurrentIndex}
      renderContent={(clip) => (
        <div className="space-y-4">
          <DynamicVideoPlayer src={clip.url} autoPlay muted loop />
          <div className="text-center">
            <h3 className="font-semibold">{clip.title}</h3>
            <p className="text-sm text-gray-600">
              {clip.startTime}s - {clip.endTime}s ({clip.duration}s)
            </p>
          </div>
        </div>
      )}
      onFavorite={async (clip) => {
        // Save to backend
        await fetch(`http://localhost:8000/clips/${clip.id}/favorite`, {
          method: "POST",
        });
      }}
    />
  );
}
```

## Styling and Customization

### Theme Integration
The component uses ShadCN UI components and Tailwind CSS classes, automatically adapting to your theme.

### Custom Styling
```tsx
<SwipeControls
  className="my-custom-container"
  // ... other props
/>
```

### Override Button Styles
Edit the Button component variants in `/home/user/supoclip/frontend/src/components/ui/button.tsx`.

## Performance Considerations

1. **Lazy Loading**: Only the current clip is rendered
2. **Animation Optimization**: Uses `AnimatePresence` for efficient transitions
3. **Event Cleanup**: All event listeners are properly cleaned up
4. **Memoization**: Use `useCallback` for handlers to prevent unnecessary re-renders

### Example with Performance Optimization

```tsx
const handleNavigate = useCallback((newIndex: number) => {
  setCurrentIndex(newIndex);
  // Optionally preload next clip
  if (newIndex < clips.length - 1) {
    const nextClip = clips[newIndex + 1];
    const video = document.createElement('video');
    video.src = nextClip.url;
  }
}, [clips]);
```

## Troubleshooting

### Gestures Not Working
- Ensure `touch-action` CSS is not blocking gestures
- Check that Framer Motion is properly installed
- Verify no parent elements are capturing events

### Keyboard Shortcuts Not Working
- Check browser console for event listener errors
- Ensure focus is not trapped in input fields
- Verify component is mounted and visible

### Animations Stuttering
- Reduce `animationDuration` for faster devices
- Check for heavy rendering in `renderContent`
- Profile React re-renders with DevTools

### Video Not Playing
- Verify video URLs are accessible
- Check CORS headers on video server
- Ensure video format is browser-compatible (H.264 MP4)

## Accessibility

- **Keyboard Navigation**: Full keyboard support
- **ARIA Labels**: All interactive elements labeled
- **Focus Management**: Proper focus indicators
- **Screen Readers**: Announces current position and actions

## Browser Support

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Examples

See `/home/user/supoclip/frontend/src/components/swipe-controls-example.tsx` for a complete working example with:
- Video player integration
- Favorite/reject tracking
- Summary statistics
- State management
- Toast notifications

## License

Part of the SupoClip project - open-source alternative to OpusClip.
