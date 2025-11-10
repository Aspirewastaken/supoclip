# SwipeControls Component - Integration Guide

## Summary

A production-ready, dual-arrow swipe controls component has been created for clip review in the SupoClip frontend. The component provides an intuitive interface for navigating through video clips with multiple interaction methods.

## Files Created

### 1. Main Component
**Location**: `/home/user/supoclip/frontend/src/components/swipe-controls.tsx`

Core component with all features:
- ✅ Left/right arrow buttons with visual feedback
- ✅ Touch and mouse swipe gesture support
- ✅ Keyboard shortcuts (arrow keys, F, Delete)
- ✅ Smooth Framer Motion animations
- ✅ Current clip counter display (e.g., "2 / 5")
- ✅ Optional favorite/reject quick action buttons
- ✅ Progress indicator dots
- ✅ Auto-hiding swipe hint
- ✅ Fully responsive and accessible

### 2. Example Implementation
**Location**: `/home/user/supoclip/frontend/src/components/swipe-controls-example.tsx`

Complete working example showing:
- State management for favorites/rejected clips
- Video player integration
- Toast notifications
- Summary statistics
- Export functionality

### 3. Demo Page
**Location**: `/home/user/supoclip/frontend/src/app/clip-review-demo/page.tsx`

Full demo page accessible at `http://localhost:3000/clip-review-demo` featuring:
- Mock video clips for testing
- Complete UI with statistics
- Keyboard shortcut hints
- Integration instructions
- Export/reset functionality

### 4. Documentation
**Location**: `/home/user/supoclip/frontend/src/components/SWIPE_CONTROLS_README.md`

Comprehensive documentation including:
- API reference
- Usage examples
- Integration patterns
- Troubleshooting guide
- Performance tips

## Dependencies Installed

```bash
npm install framer-motion
```

Framer Motion has been added to the project for smooth, physics-based animations.

## Quick Start

### Basic Usage

```tsx
import { useState } from "react";
import SwipeControls from "@/components/swipe-controls";

function ClipReview({ clips }) {
  const [currentIndex, setCurrentIndex] = useState(0);

  return (
    <SwipeControls
      clips={clips}
      currentIndex={currentIndex}
      onNavigate={setCurrentIndex}
      renderContent={(clip) => (
        <video src={clip.url} controls autoPlay loop />
      )}
    />
  );
}
```

### Integration with Backend API

```tsx
// Fetch clips from SupoClip backend
const response = await fetch(`http://localhost:8000/tasks/${taskId}/clips`);
const data = await response.json();

const clips = data.map((clip) => ({
  id: clip.id,
  url: `http://localhost:8000/clips/${clip.filename}`,
  title: clip.segment_text?.substring(0, 50),
  duration: clip.duration,
}));

<SwipeControls
  clips={clips}
  currentIndex={currentIndex}
  onNavigate={setCurrentIndex}
  renderContent={(clip) => (
    <DynamicVideoPlayer src={clip.url} autoPlay muted loop />
  )}
  onFavorite={(clip) => {
    // Save to backend or local state
    console.log("Favorited:", clip.id);
  }}
  onReject={(clip) => {
    // Mark as rejected
    console.log("Rejected:", clip.id);
  }}
/>
```

## Component Props

### Required
- `clips`: Array of clip objects with `id` and `url`
- `currentIndex`: Current clip index (0-based)
- `onNavigate`: Callback when navigating to new clip
- `renderContent`: Function to render clip content

### Optional
- `onFavorite`: Callback when favoriting a clip
- `onReject`: Callback when rejecting a clip
- `showQuickActions`: Show favorite/reject buttons (default: true)
- `swipeThreshold`: Pixels to trigger swipe (default: 50)
- `animationDuration`: Animation duration in seconds (default: 0.3)
- `className`: Additional CSS classes

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| ← Left Arrow | Previous clip |
| → Right Arrow | Next clip |
| F | Favorite current clip |
| Delete/Backspace | Reject current clip |

## Gesture Controls

- **Swipe/Drag Left**: Next clip
- **Swipe/Drag Right**: Previous clip
- Works with both touch and mouse

## UI Elements

### 1. Counter Display
- Fixed at top-center
- Shows "X / Total" format
- Black background with blur

### 2. Navigation Arrows
- Large circular buttons on sides
- Auto-hide at start/end
- Smooth transitions

### 3. Quick Action Buttons
- Heart icon for favorite
- X icon for reject
- Fixed at top-right
- Only shown if handlers provided

### 4. Progress Dots
- Bottom-center position
- One dot per clip
- Click to jump to clip
- Active dot expands

### 5. Swipe Hint
- Shows on first clip
- "Swipe or use arrow keys"
- Fades after 2 seconds

## Integration Examples

### Example 1: Simple Clip Navigation

```tsx
import SwipeControls from "@/components/swipe-controls";

const clips = [
  { id: "1", url: "/clips/clip1.mp4" },
  { id: "2", url: "/clips/clip2.mp4" },
];

function SimpleReview() {
  const [currentIndex, setCurrentIndex] = useState(0);

  return (
    <SwipeControls
      clips={clips}
      currentIndex={currentIndex}
      onNavigate={setCurrentIndex}
      renderContent={(clip) => (
        <video src={clip.url} controls className="w-full" />
      )}
    />
  );
}
```

### Example 2: With DynamicVideoPlayer

```tsx
import SwipeControls from "@/components/swipe-controls";
import DynamicVideoPlayer from "@/components/dynamic-video-player";

function VideoReview({ clips }) {
  const [currentIndex, setCurrentIndex] = useState(0);

  return (
    <SwipeControls
      clips={clips}
      currentIndex={currentIndex}
      onNavigate={setCurrentIndex}
      renderContent={(clip) => (
        <DynamicVideoPlayer
          src={clip.url}
          autoPlay
          muted
          loop
          className="mx-auto"
        />
      )}
    />
  );
}
```

### Example 3: Full-Featured Review

```tsx
import SwipeControls from "@/components/swipe-controls";
import { toast } from "sonner";

function FullReview({ clips }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [favorites, setFavorites] = useState(new Set());

  return (
    <SwipeControls
      clips={clips}
      currentIndex={currentIndex}
      onNavigate={setCurrentIndex}
      onFavorite={(clip) => {
        const newFaves = new Set(favorites);
        newFaves.add(clip.id);
        setFavorites(newFaves);
        toast.success("Added to favorites!");
      }}
      onReject={(clip) => {
        toast.error("Rejected clip");
        // Move to next clip
        if (currentIndex < clips.length - 1) {
          setCurrentIndex(currentIndex + 1);
        }
      }}
      renderContent={(clip) => (
        <div className="space-y-4">
          <DynamicVideoPlayer src={clip.url} autoPlay muted loop />
          <h3 className="text-center font-bold">{clip.title}</h3>
        </div>
      )}
      showQuickActions={true}
      swipeThreshold={50}
      animationDuration={0.3}
    />
  );
}
```

## Testing the Component

### Option 1: Demo Page
```bash
# Start backend
cd backend
uvicorn src.main:app --reload

# Start frontend
cd frontend
npm run dev

# Visit: http://localhost:3000/clip-review-demo
```

### Option 2: Integration with Existing Task Page
Add to `/home/user/supoclip/frontend/src/app/tasks/[id]/page.tsx`:

```tsx
import SwipeControls from "@/components/swipe-controls";

// In your task detail page:
<SwipeControls
  clips={taskClips}
  currentIndex={currentClipIndex}
  onNavigate={setCurrentClipIndex}
  renderContent={(clip) => (
    <DynamicVideoPlayer src={clip.url} autoPlay muted loop />
  )}
  onFavorite={handleFavoriteClip}
/>
```

## Styling and Customization

### Theme Support
The component uses ShadCN UI components and automatically adapts to light/dark themes.

### Custom Styling
```tsx
<SwipeControls
  className="my-8 max-w-4xl mx-auto"
  // ... other props
/>
```

### Button Customization
Modify button styles in `/home/user/supoclip/frontend/src/components/ui/button.tsx`.

## Performance Considerations

1. **Lazy Loading**: Only current clip is rendered
2. **Animation Optimization**: Uses AnimatePresence for efficient transitions
3. **Event Cleanup**: All listeners properly removed on unmount
4. **Gesture Detection**: Optimized drag handling with Framer Motion

### Performance Tips

```tsx
// Memoize callbacks
const handleNavigate = useCallback((newIndex) => {
  setCurrentIndex(newIndex);
}, []);

// Preload next clip
const handleNavigate = useCallback((newIndex) => {
  setCurrentIndex(newIndex);
  if (newIndex < clips.length - 1) {
    const nextClip = clips[newIndex + 1];
    const video = document.createElement('video');
    video.src = nextClip.url;
  }
}, [clips]);
```

## Accessibility Features

- ✅ Full keyboard navigation
- ✅ ARIA labels on all interactive elements
- ✅ Focus indicators
- ✅ Screen reader announcements
- ✅ Semantic HTML structure

## Browser Support

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

### Issue: Gestures not working
**Solution**: Ensure no parent elements have `touch-action: none`

### Issue: Keyboard shortcuts not responding
**Solution**: Check that focus is not trapped in input fields

### Issue: Animations stuttering
**Solution**: Reduce `animationDuration` or check for heavy rendering

### Issue: Videos not playing
**Solution**: Verify CORS headers and video format (H.264 MP4)

## Next Steps

1. **Test the demo page**: Visit `/clip-review-demo` to see the component in action
2. **Review the example**: Check `swipe-controls-example.tsx` for implementation patterns
3. **Integrate with tasks**: Add to your task detail page
4. **Customize styling**: Adjust colors and animations to match your brand
5. **Add backend integration**: Connect favorite/reject actions to API

## API Backend Integration

### Endpoint Examples

```typescript
// Fetch clips
GET /tasks/{taskId}/clips

// Mark as favorite
POST /clips/{clipId}/favorite

// Mark as rejected
POST /clips/{clipId}/reject

// Get clip file
GET /clips/{filename}
```

### Example API Integration

```tsx
async function saveClipPreference(clipId: string, action: "favorite" | "reject") {
  try {
    const response = await fetch(`http://localhost:8000/clips/${clipId}/${action}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      toast.success(`Clip ${action}d successfully!`);
    }
  } catch (error) {
    console.error(`Failed to ${action} clip:`, error);
    toast.error(`Failed to ${action} clip`);
  }
}

// Use in component
<SwipeControls
  onFavorite={(clip) => saveClipPreference(clip.id, "favorite")}
  onReject={(clip) => saveClipPreference(clip.id, "reject")}
/>
```

## Component Architecture

```
SwipeControls
├── Counter Display (top-center)
├── Quick Actions (top-right)
│   ├── Favorite Button
│   └── Reject Button
├── Content Area
│   ├── AnimatePresence wrapper
│   ├── Motion.div (swipeable)
│   └── renderContent() output
├── Navigation Arrows (sides)
│   ├── Left Arrow
│   └── Right Arrow
├── Progress Dots (bottom)
└── Swipe Hint (auto-fade)
```

## File Locations Reference

- **Component**: `/home/user/supoclip/frontend/src/components/swipe-controls.tsx`
- **Example**: `/home/user/supoclip/frontend/src/components/swipe-controls-example.tsx`
- **Demo Page**: `/home/user/supoclip/frontend/src/app/clip-review-demo/page.tsx`
- **Documentation**: `/home/user/supoclip/frontend/src/components/SWIPE_CONTROLS_README.md`
- **Integration Guide**: `/home/user/supoclip/SWIPE_CONTROLS_INTEGRATION_GUIDE.md` (this file)

## Support and Customization

For further customization or issues:
1. Check the comprehensive README at `/frontend/src/components/SWIPE_CONTROLS_README.md`
2. Review the example implementation
3. Test with the demo page
4. Modify button styles in `/components/ui/button.tsx`
5. Adjust animations by changing `animationDuration` and Framer Motion variants

---

**Created**: 2025-11-10
**Component Version**: 1.0
**Dependencies**: React 19, Framer Motion, ShadCN UI, Lucide Icons
