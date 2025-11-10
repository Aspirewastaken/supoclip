# Voice Dictation Component

A React component for voice-to-text dictation using the Web Speech API. Perfect for hands-free input, accessibility improvements, and enhancing user experience with speech recognition.

## Features

- **Web Speech API Integration**: Leverages browser native speech recognition
- **Real-time Transcription**: See text as you speak with interim results
- **Visual Feedback**: Animated recording indicator with pulse effect
- **Error Handling**: Comprehensive error messages for all failure scenarios
- **Browser Support Detection**: Gracefully degrades on unsupported browsers
- **TypeScript Support**: Full type safety with proper interfaces
- **Customizable**: Supports multiple languages and configuration options
- **Two Integration Modes**: Standalone button or integrated input component

## Browser Support

The Web Speech API is supported in:

- ✅ Google Chrome (Desktop & Android)
- ✅ Microsoft Edge
- ✅ Safari (macOS & iOS 14.5+)
- ✅ Samsung Internet
- ❌ Firefox (not supported)

Users on unsupported browsers will see a disabled microphone icon.

## Installation

The component is already included in your project at:
```
/home/user/supoclip/frontend/src/components/voice-dictation.tsx
```

No additional dependencies required beyond what's already in `package.json`.

## Quick Start

### Option 1: Standalone Voice Button

Use when you want full control over text integration:

```tsx
import { VoiceDictation } from "@/components/voice-dictation"
import { Input } from "@/components/ui/input"
import { useState } from "react"

function MyForm() {
  const [title, setTitle] = useState("")

  const handleTranscript = (text: string) => {
    setTitle(prev => prev ? `${prev} ${text}` : text)
  }

  return (
    <div className="flex items-center gap-2">
      <Input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Enter title..."
      />
      <VoiceDictation
        onTranscript={handleTranscript}
        onError={(error) => console.error(error)}
      />
    </div>
  )
}
```

### Option 2: Integrated Input Component

Drop-in replacement for standard inputs with built-in voice:

```tsx
import { VoiceDictationInput } from "@/components/voice-dictation"
import { useState } from "react"

function MyForm() {
  const [title, setTitle] = useState("")

  return (
    <VoiceDictationInput
      value={title}
      onChange={(e) => setTitle(e.target.value)}
      onVoiceTranscript={(text) => setTitle(text)}
      placeholder="Enter or speak title..."
      voiceButtonPosition="right"
      className="w-full rounded-md border px-3 py-2"
    />
  )
}
```

## Component API

### VoiceDictation Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `onTranscript` | `(text: string) => void` | Required | Callback fired when speech is recognized |
| `onError` | `(error: string) => void` | Optional | Callback fired on errors |
| `className` | `string` | Optional | Additional CSS classes |
| `language` | `string` | `"en-US"` | Language code for recognition |
| `continuous` | `boolean` | `false` | Keep listening until manually stopped |
| `interimResults` | `boolean` | `true` | Show real-time interim text |

### VoiceDictationInput Props

Inherits all standard `<input>` props, plus:

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `onVoiceTranscript` | `(text: string) => void` | Optional | Callback for voice updates |
| `showVoiceButton` | `boolean` | `true` | Show/hide voice button |
| `voiceButtonPosition` | `"left" \| "right"` | `"right"` | Button position |
| `language` | `string` | `"en-US"` | Language code |

## Language Support

Common language codes:

```tsx
// English (US)
<VoiceDictation language="en-US" />

// English (UK)
<VoiceDictation language="en-GB" />

// Spanish (Spain)
<VoiceDictation language="es-ES" />

// French
<VoiceDictation language="fr-FR" />

// German
<VoiceDictation language="de-DE" />

// Japanese
<VoiceDictation language="ja-JP" />

// Chinese (Simplified)
<VoiceDictation language="zh-CN" />
```

[Full list of language codes](https://cloud.google.com/speech-to-text/docs/languages)

## Advanced Usage

### Continuous Recording

For longer dictation sessions:

```tsx
<VoiceDictation
  onTranscript={(text) => setTranscript(prev => [...prev, text])}
  continuous={true}
  interimResults={true}
/>
```

### Custom Error Handling

```tsx
<VoiceDictation
  onTranscript={handleTranscript}
  onError={(error) => {
    // Custom error handling
    if (error.includes("not-allowed")) {
      alert("Please allow microphone access")
    }
    // Log to analytics
    logError("voice-dictation", error)
  }}
/>
```

### Form Integration

```tsx
function VideoUploadForm() {
  const [formData, setFormData] = useState({
    title: "",
    description: ""
  })

  const updateField = (field: string) => (text: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field] ? `${prev[field]} ${text}` : text
    }))
  }

  return (
    <form>
      <div className="space-y-2">
        <Label>Title</Label>
        <div className="flex gap-2">
          <Input
            value={formData.title}
            onChange={(e) => updateField("title")(e.target.value)}
          />
          <VoiceDictation onTranscript={updateField("title")} />
        </div>
      </div>

      <div className="space-y-2">
        <Label>Description</Label>
        <div className="flex gap-2">
          <Input
            value={formData.description}
            onChange={(e) => updateField("description")(e.target.value)}
          />
          <VoiceDictation onTranscript={updateField("description")} />
        </div>
      </div>
    </form>
  )
}
```

## Error Types

The component handles these error cases:

- `no-speech`: No speech detected
- `audio-capture`: No microphone found
- `not-allowed`: Microphone permission denied
- `network`: Network error during recognition
- `aborted`: Recognition was aborted

All errors provide user-friendly messages via the `onError` callback.

## Styling

The component uses TailwindCSS and follows ShadCN UI patterns:

```tsx
// Custom button styling
<VoiceDictation
  className="my-custom-class"
  onTranscript={handleTranscript}
/>

// The button state provides visual feedback:
// - Default: Outline variant with MicOff icon
// - Recording: Destructive variant with Mic icon + pulse animation
// - Disabled: Grayed out (unsupported browser)
```

## Testing

### Manual Testing

1. Open your app in Chrome/Edge/Safari
2. Click the microphone button
3. Allow microphone access when prompted
4. Speak clearly into your microphone
5. Watch text appear in real-time
6. Click again to stop recording

### Automated Testing

```tsx
// Mock Web Speech API in tests
global.window.SpeechRecognition = class MockSpeechRecognition {
  // Mock implementation
}
```

## Troubleshooting

### Microphone Not Working

1. Check browser permissions (chrome://settings/content/microphone)
2. Ensure HTTPS connection (required for microphone access)
3. Test microphone in system settings
4. Try a different browser

### Text Not Appearing

1. Check `onTranscript` callback is properly connected
2. Ensure state updates are working
3. Speak more clearly or closer to microphone
4. Check browser console for errors

### Browser Says "Not Supported"

1. Confirm using Chrome, Edge, or Safari
2. Update browser to latest version
3. Check if running over HTTPS (required)

## Examples

See `/home/user/supoclip/frontend/src/components/voice-dictation-example.tsx` for:

- ✅ Manual integration example
- ✅ Integrated component example
- ✅ Complete form example
- ✅ Continuous recording example
- ✅ Full demo page

## Integration with SupoClip

### Suggested Integration Points

1. **Video Upload Form** - Title and description fields
2. **Clip Editing** - Rename clips with voice
3. **Task Creation** - Voice-enabled task naming
4. **Settings** - Voice-controlled preferences

### Example: Add to Video Upload

```tsx
// In your video upload component
import { VoiceDictation } from "@/components/voice-dictation"

<div className="flex items-center gap-2">
  <Input
    placeholder="Video title..."
    value={title}
    onChange={(e) => setTitle(e.target.value)}
  />
  <VoiceDictation
    onTranscript={(text) => setTitle(prev => prev ? `${prev} ${text}` : text)}
    language="en-US"
  />
</div>
```

## Future Enhancements

Potential improvements for future versions:

- [ ] Save audio recordings to backend
- [ ] Offline speech recognition fallback
- [ ] Custom wake words
- [ ] Voice commands (e.g., "new line", "period")
- [ ] Multiple language switching
- [ ] Speaker identification
- [ ] Noise cancellation

## Resources

- [Web Speech API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [SpeechRecognition Interface](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition)
- [Browser Compatibility](https://caniuse.com/speech-recognition)
- [Language Support](https://cloud.google.com/speech-to-text/docs/languages)

## License

Same as SupoClip project (see root LICENSE file).

## Support

For issues or questions:
1. Check this documentation
2. Review example implementations
3. Check browser console for errors
4. Open an issue on GitHub
