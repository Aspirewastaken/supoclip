"use client"

/**
 * Voice Dictation Component - Usage Examples
 *
 * This file demonstrates different ways to use the VoiceDictation component
 * in your application for voice-to-text input.
 */

import * as React from "react"
import { VoiceDictation, VoiceDictationInput } from "./voice-dictation"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

/**
 * Example 1: Standalone Voice Button with Manual Input Control
 *
 * Use this approach when you want full control over how the transcribed
 * text is integrated with your input field.
 */
export function VoiceDictationExample1() {
  const [title, setTitle] = React.useState("")

  const handleTranscript = (text: string) => {
    // Append the transcribed text to existing title
    setTitle((prev) => (prev ? `${prev} ${text}` : text))
  }

  const handleError = (error: string) => {
    console.error("Voice dictation error:", error)
    alert(error)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Example 1: Manual Integration</CardTitle>
        <CardDescription>
          Voice button separate from input with custom text handling
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="title-1">Video Title</Label>
          <div className="flex items-center gap-2">
            <Input
              id="title-1"
              placeholder="Enter or speak your title..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="flex-1"
            />
            <VoiceDictation
              onTranscript={handleTranscript}
              onError={handleError}
              language="en-US"
            />
          </div>
        </div>
        <p className="text-sm text-muted-foreground">
          Current title: {title || "(empty)"}
        </p>
      </CardContent>
    </Card>
  )
}

/**
 * Example 2: Integrated Voice Input Component
 *
 * Use this all-in-one component when you want a simple drop-in
 * replacement for a standard input field with voice capabilities.
 */
export function VoiceDictationExample2() {
  const [title, setTitle] = React.useState("")

  return (
    <Card>
      <CardHeader>
        <CardTitle>Example 2: Integrated Component</CardTitle>
        <CardDescription>
          All-in-one input with built-in voice dictation
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="title-2">Video Title</Label>
          <VoiceDictationInput
            id="title-2"
            placeholder="Enter or speak your title..."
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onVoiceTranscript={(text) => setTitle(text)}
            voiceButtonPosition="right"
            language="en-US"
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>
        <p className="text-sm text-muted-foreground">
          Current title: {title || "(empty)"}
        </p>
      </CardContent>
    </Card>
  )
}

/**
 * Example 3: Form with Multiple Voice Inputs
 *
 * Demonstrates using voice dictation in a complete form with
 * multiple input fields.
 */
export function VoiceDictationExample3() {
  const [formData, setFormData] = React.useState({
    title: "",
    description: "",
    tags: "",
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log("Form submitted:", formData)
    alert(JSON.stringify(formData, null, 2))
  }

  const updateField = (field: keyof typeof formData) => (value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Example 3: Complete Form</CardTitle>
        <CardDescription>
          Multiple voice-enabled inputs in a single form
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title-3">Title</Label>
            <div className="flex items-center gap-2">
              <Input
                id="title-3"
                placeholder="Video title..."
                value={formData.title}
                onChange={(e) => updateField("title")(e.target.value)}
                required
              />
              <VoiceDictation
                onTranscript={updateField("title")}
                language="en-US"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description-3">Description</Label>
            <div className="flex items-center gap-2">
              <Input
                id="description-3"
                placeholder="Video description..."
                value={formData.description}
                onChange={(e) => updateField("description")(e.target.value)}
              />
              <VoiceDictation
                onTranscript={updateField("description")}
                language="en-US"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="tags-3">Tags</Label>
            <div className="flex items-center gap-2">
              <Input
                id="tags-3"
                placeholder="Comma-separated tags..."
                value={formData.tags}
                onChange={(e) => updateField("tags")(e.target.value)}
              />
              <VoiceDictation
                onTranscript={updateField("tags")}
                language="en-US"
              />
            </div>
          </div>

          <Button type="submit">Submit Form</Button>
        </form>
      </CardContent>
    </Card>
  )
}

/**
 * Example 4: Continuous Recording Mode
 *
 * Demonstrates continuous recording where the microphone stays active
 * until manually stopped, useful for longer dictation sessions.
 */
export function VoiceDictationExample4() {
  const [transcript, setTranscript] = React.useState<string[]>([])
  const [error, setError] = React.useState<string | null>(null)

  const handleTranscript = (text: string) => {
    setTranscript((prev) => [...prev, text])
  }

  const handleError = (errorMessage: string) => {
    setError(errorMessage)
    setTimeout(() => setError(null), 5000)
  }

  const clearTranscript = () => {
    setTranscript([])
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Example 4: Continuous Recording</CardTitle>
        <CardDescription>
          Keep recording until you stop manually - great for long dictation
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <VoiceDictation
            onTranscript={handleTranscript}
            onError={handleError}
            continuous={true}
            interimResults={true}
            language="en-US"
          />
          <Button variant="outline" onClick={clearTranscript} size="sm">
            Clear
          </Button>
        </div>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="space-y-2">
          <Label>Transcript ({transcript.length} segments)</Label>
          <div className="min-h-[100px] rounded-md border bg-muted/30 p-3 text-sm">
            {transcript.length > 0 ? (
              transcript.join(" ")
            ) : (
              <span className="text-muted-foreground">
                Start speaking to see your transcript here...
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Complete Demo Page Component
 *
 * Renders all examples in a scrollable container
 */
export function VoiceDictationDemo() {
  return (
    <div className="container mx-auto py-8 space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">
          Voice Dictation Component Examples
        </h1>
        <p className="text-muted-foreground">
          Click the microphone button to start voice dictation. Make sure to allow
          microphone access when prompted.
        </p>
      </div>

      <VoiceDictationExample1 />
      <VoiceDictationExample2 />
      <VoiceDictationExample3 />
      <VoiceDictationExample4 />

      <Card>
        <CardHeader>
          <CardTitle>Browser Support</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-2">
          <p>
            The Web Speech API is supported in the following browsers:
          </p>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground">
            <li>Google Chrome (Desktop & Android)</li>
            <li>Microsoft Edge</li>
            <li>Safari (macOS & iOS)</li>
            <li>Samsung Internet</li>
          </ul>
          <p className="text-muted-foreground mt-4">
            Note: Firefox does not currently support the Web Speech API for voice
            recognition. Users on unsupported browsers will see a disabled microphone
            button.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
