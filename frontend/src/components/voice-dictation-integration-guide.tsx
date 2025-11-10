"use client"

/**
 * Voice Dictation Integration Guide for SupoClip
 *
 * This file shows exactly how to integrate voice dictation into existing
 * SupoClip forms with minimal changes to current code.
 */

import { useState } from "react"
import { VoiceDictation } from "./voice-dictation"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"

/**
 * INTEGRATION EXAMPLE 1: Add Voice to Video URL Input
 *
 * Before:
 * ```tsx
 * <Input
 *   placeholder="Paste YouTube URL here..."
 *   value={url}
 *   onChange={(e) => setUrl(e.target.value)}
 * />
 * ```
 *
 * After:
 * ```tsx
 * <div className="flex items-center gap-2">
 *   <Input
 *     placeholder="Paste or speak YouTube URL..."
 *     value={url}
 *     onChange={(e) => setUrl(e.target.value)}
 *     className="flex-1"
 *   />
 *   <VoiceDictation
 *     onTranscript={(text) => setUrl(prev => prev ? `${prev} ${text}` : text)}
 *     language="en-US"
 *   />
 * </div>
 * ```
 */
export function VideoUrlInputWithVoice() {
  const [url, setUrl] = useState("")

  return (
    <div className="space-y-2">
      <Label htmlFor="video-url">YouTube URL</Label>
      <div className="flex items-center gap-2">
        <Input
          id="video-url"
          placeholder="Paste or speak YouTube URL..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="flex-1"
        />
        <VoiceDictation
          onTranscript={(text) => setUrl(prev => prev ? `${prev} ${text}` : text)}
          language="en-US"
        />
      </div>
    </div>
  )
}

/**
 * INTEGRATION EXAMPLE 2: Add Voice to Task Title Input
 *
 * For when users want to name their video processing task
 */
export function TaskTitleInputWithVoice() {
  const [title, setTitle] = useState("")

  return (
    <div className="space-y-2">
      <Label htmlFor="task-title">Task Title (Optional)</Label>
      <div className="flex items-center gap-2">
        <Input
          id="task-title"
          placeholder="Enter or speak a name for this task..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="flex-1"
        />
        <VoiceDictation
          onTranscript={(text) => setTitle(prev => prev ? `${prev} ${text}` : text)}
          language="en-US"
        />
      </div>
      <p className="text-xs text-muted-foreground">
        Give this task a memorable name for easy identification
      </p>
    </div>
  )
}

/**
 * INTEGRATION EXAMPLE 3: Complete Video Upload Form with Voice
 *
 * Shows a complete form implementation with multiple voice-enabled fields
 */
export function CompleteVideoFormWithVoice() {
  const [formData, setFormData] = useState({
    url: "",
    title: "",
    description: "",
  })
  const [isLoading, setIsLoading] = useState(false)

  const updateField = (field: keyof typeof formData) => (value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await fetch("http://localhost:8000/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source: { url: formData.url },
          title: formData.title || undefined,
          description: formData.description || undefined,
        }),
      })

      if (!response.ok) throw new Error("Failed to start processing")

      const data = await response.json()
      console.log("Task started:", data)
    } catch (error) {
      console.error("Error:", error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* YouTube URL with Voice */}
      <div className="space-y-2">
        <Label htmlFor="url">YouTube URL *</Label>
        <div className="flex items-center gap-2">
          <Input
            id="url"
            placeholder="Paste or speak YouTube URL..."
            value={formData.url}
            onChange={(e) => updateField("url")(e.target.value)}
            className="flex-1"
            required
          />
          <VoiceDictation
            onTranscript={(text) => {
              // Clean up the URL if needed
              const cleanedUrl = text.trim()
              updateField("url")(cleanedUrl)
            }}
            language="en-US"
          />
        </div>
      </div>

      {/* Title with Voice */}
      <div className="space-y-2">
        <Label htmlFor="title">Custom Title (Optional)</Label>
        <div className="flex items-center gap-2">
          <Input
            id="title"
            placeholder="Enter or speak a custom title..."
            value={formData.title}
            onChange={(e) => updateField("title")(e.target.value)}
            className="flex-1"
          />
          <VoiceDictation
            onTranscript={(text) => updateField("title")(text)}
            language="en-US"
          />
        </div>
        <p className="text-xs text-muted-foreground">
          Leave blank to use the video's original title
        </p>
      </div>

      {/* Description with Voice */}
      <div className="space-y-2">
        <Label htmlFor="description">Description (Optional)</Label>
        <div className="flex items-center gap-2">
          <Input
            id="description"
            placeholder="Enter or speak a description..."
            value={formData.description}
            onChange={(e) => updateField("description")(e.target.value)}
            className="flex-1"
          />
          <VoiceDictation
            onTranscript={(text) => updateField("description")(text)}
            continuous={true} // Allow continuous recording for longer descriptions
            language="en-US"
          />
        </div>
      </div>

      <Button type="submit" disabled={isLoading || !formData.url}>
        {isLoading ? "Processing..." : "Start Processing"}
      </Button>
    </form>
  )
}

/**
 * INTEGRATION EXAMPLE 4: Clip Rename with Voice
 *
 * For renaming generated clips
 */
export function ClipRenameWithVoice() {
  const [clipName, setClipName] = useState("")

  const handleSave = () => {
    console.log("Saving clip name:", clipName)
    // API call to update clip name
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="clip-name">Clip Name</Label>
        <div className="flex items-center gap-2">
          <Input
            id="clip-name"
            placeholder="Enter or speak new clip name..."
            value={clipName}
            onChange={(e) => setClipName(e.target.value)}
            className="flex-1"
          />
          <VoiceDictation
            onTranscript={(text) => setClipName(text)}
            language="en-US"
          />
        </div>
      </div>
      <Button onClick={handleSave} disabled={!clipName}>
        Save Changes
      </Button>
    </div>
  )
}

/**
 * QUICK COPY-PASTE SNIPPETS
 *
 * Just copy these snippets into your existing code:
 */

export const QUICK_SNIPPETS = {
  // 1. Import statement (add to top of file)
  import_statement: `import { VoiceDictation } from "@/components/voice-dictation"`,

  // 2. Wrap existing input (minimal change)
  wrap_input: `
<div className="flex items-center gap-2">
  <Input
    {...existingProps}
    className="flex-1"
  />
  <VoiceDictation
    onTranscript={(text) => setYourState(prev => prev ? \`\${prev} \${text}\` : text)}
    language="en-US"
  />
</div>
  `,

  // 3. Replace input text
  replace_text: `
<VoiceDictation
  onTranscript={(text) => setValue(text)}
  language="en-US"
/>
  `,

  // 4. Append to input text
  append_text: `
<VoiceDictation
  onTranscript={(text) => setValue(prev => prev ? \`\${prev} \${text}\` : text)}
  language="en-US"
/>
  `,

  // 5. With error handling
  with_error: `
<VoiceDictation
  onTranscript={(text) => setValue(text)}
  onError={(error) => {
    console.error("Voice error:", error)
    alert(error)
  }}
  language="en-US"
/>
  `,

  // 6. Continuous mode (for long text)
  continuous: `
<VoiceDictation
  onTranscript={(text) => setValue(prev => [...prev, text])}
  continuous={true}
  interimResults={true}
  language="en-US"
/>
  `,
}

/**
 * STEP-BY-STEP INTEGRATION INTO page.tsx
 *
 * 1. Add import at top:
 *    import { VoiceDictation } from "@/components/voice-dictation"
 *
 * 2. Find the URL input section (around line 450):
 *    Replace:
 *      <Input
 *        placeholder="Paste YouTube URL here..."
 *        value={url}
 *        onChange={(e) => setUrl(e.target.value)}
 *      />
 *
 *    With:
 *      <div className="flex items-center gap-2">
 *        <Input
 *          placeholder="Paste or speak YouTube URL..."
 *          value={url}
 *          onChange={(e) => setUrl(e.target.value)}
 *          className="flex-1"
 *        />
 *        <VoiceDictation
 *          onTranscript={(text) => setUrl(prev => prev ? `${prev} ${text}` : text)}
 *          language="en-US"
 *        />
 *      </div>
 *
 * 3. Test it:
 *    - Open the app in Chrome/Edge/Safari
 *    - Click the microphone button
 *    - Allow microphone access
 *    - Speak a YouTube URL or title
 *    - Watch it appear in the input!
 *
 * That's it! Three simple steps to add voice dictation.
 */

export default function IntegrationGuide() {
  return (
    <div className="container mx-auto py-8 space-y-8 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold mb-2">
          Voice Dictation Integration Guide
        </h1>
        <p className="text-muted-foreground">
          Copy-paste examples for integrating voice dictation into SupoClip
        </p>
      </div>

      <div className="space-y-8">
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">1. Video URL Input</h2>
          <VideoUrlInputWithVoice />
        </div>

        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">2. Task Title Input</h2>
          <TaskTitleInputWithVoice />
        </div>

        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">3. Complete Form</h2>
          <CompleteVideoFormWithVoice />
        </div>

        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">4. Clip Rename</h2>
          <ClipRenameWithVoice />
        </div>
      </div>
    </div>
  )
}
