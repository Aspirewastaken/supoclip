"use client"

import React, { useState } from "react"
import { VideoPreview, type VideoSource } from "./video-preview"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Checkbox } from "@/components/ui/checkbox"

/**
 * Comprehensive demonstration of the VideoPreview component
 * Shows all features and use cases
 */
export function VideoPreviewDemo() {
  // Demo configuration
  const [demoMode, setDemoMode] = useState<
    "single" | "trimming" | "comparison" | "mobile"
  >("single")
  const [enableTrimming, setEnableTrimming] = useState(false)
  const [showFrameNumber, setShowFrameNumber] = useState(false)
  const [autoPlay, setAutoPlay] = useState(false)
  const [trimRange, setTrimRange] = useState<[number, number]>([2, 8])
  const [currentTime, setCurrentTime] = useState(0)

  // Example video sources (replace with your actual video URLs)
  const singleVideo: VideoSource = {
    id: "demo-clip-1",
    url: "http://localhost:8000/clips/example-clip-1.mp4",
    label: "Demo Clip",
  }

  const comparisonVideos: VideoSource[] = [
    {
      id: "original",
      url: "http://localhost:8000/clips/original.mp4",
      label: "Original",
    },
    {
      id: "variation-1",
      url: "http://localhost:8000/clips/variation-1.mp4",
      label: "With Subtitles",
    },
  ]

  const handleTrimChange = (start: number, end: number) => {
    console.log("Trim changed:", { start, end })
    setTrimRange([start, end])
  }

  const handleTimeUpdate = (time: number) => {
    setCurrentTime(time)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold">Video Preview Component</h1>
          <p className="text-gray-600">
            A full-featured video player with timeline scrubbing, frame-by-frame
            navigation, and more
          </p>
        </div>

        {/* Demo Mode Selector */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Demo Mode</h2>
          <div className="flex gap-2 flex-wrap">
            <Button
              variant={demoMode === "single" ? "default" : "outline"}
              onClick={() => setDemoMode("single")}
            >
              Single Video
            </Button>
            <Button
              variant={demoMode === "trimming" ? "default" : "outline"}
              onClick={() => setDemoMode("trimming")}
            >
              Video Trimming
            </Button>
            <Button
              variant={demoMode === "comparison" ? "default" : "outline"}
              onClick={() => setDemoMode("comparison")}
            >
              Side-by-Side Comparison
            </Button>
            <Button
              variant={demoMode === "mobile" ? "default" : "outline"}
              onClick={() => setDemoMode("mobile")}
            >
              Mobile View
            </Button>
          </div>
        </Card>

        {/* Configuration Panel */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Configuration</h2>
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="enable-trimming"
                checked={enableTrimming}
                onCheckedChange={(checked) =>
                  setEnableTrimming(checked as boolean)
                }
              />
              <label
                htmlFor="enable-trimming"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Enable Trimming
              </label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="show-frame-number"
                checked={showFrameNumber}
                onCheckedChange={(checked) =>
                  setShowFrameNumber(checked as boolean)
                }
              />
              <label
                htmlFor="show-frame-number"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Show Frame Number
              </label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="auto-play"
                checked={autoPlay}
                onCheckedChange={(checked) => setAutoPlay(checked as boolean)}
              />
              <label
                htmlFor="auto-play"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Auto Play
              </label>
            </div>

            {enableTrimming && (
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-900">
                  Trim Range: {trimRange[0].toFixed(2)}s -{" "}
                  {trimRange[1].toFixed(2)}s (Duration:{" "}
                  {(trimRange[1] - trimRange[0]).toFixed(2)}s)
                </p>
              </div>
            )}

            <div className="p-4 bg-gray-100 rounded-lg">
              <p className="text-sm text-gray-700">
                Current Time: {currentTime.toFixed(2)}s
              </p>
            </div>
          </div>
        </Card>

        {/* Video Preview Area */}
        <Card className="p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              {demoMode === "single" && "Single Video Preview"}
              {demoMode === "trimming" && "Video Trimming Mode"}
              {demoMode === "comparison" && "Side-by-Side Comparison"}
              {demoMode === "mobile" && "Mobile-Optimized View"}
            </h2>
            <Badge variant="outline">
              {demoMode.charAt(0).toUpperCase() + demoMode.slice(1)}
            </Badge>
          </div>

          <Separator className="mb-6" />

          {/* Single Video Mode */}
          {demoMode === "single" && (
            <VideoPreview
              sources={singleVideo}
              enableTrimming={enableTrimming}
              showFrameNumber={showFrameNumber}
              autoPlay={autoPlay}
              trimRange={enableTrimming ? trimRange : undefined}
              onTrimChange={handleTrimChange}
              onTimeUpdate={handleTimeUpdate}
              thumbnailInterval={1}
            />
          )}

          {/* Trimming Mode */}
          {demoMode === "trimming" && (
            <div className="space-y-4">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="font-semibold text-yellow-900 mb-2">
                  How to Trim:
                </h3>
                <ul className="text-sm text-yellow-800 space-y-1">
                  <li>
                    1. Click and drag the blue handles on the timeline to adjust
                    the trim range
                  </li>
                  <li>
                    2. The darkened areas show what will be trimmed out
                  </li>
                  <li>
                    3. Playback will automatically loop within the trim range
                  </li>
                  <li>
                    4. Use the scissors icons on the handles for precise
                    adjustments
                  </li>
                </ul>
              </div>

              <VideoPreview
                sources={singleVideo}
                enableTrimming={true}
                showFrameNumber={true}
                autoPlay={autoPlay}
                trimRange={trimRange}
                onTrimChange={handleTrimChange}
                onTimeUpdate={handleTimeUpdate}
                thumbnailInterval={0.5}
              />

              <div className="flex gap-2">
                <Button onClick={() => console.log("Export trim:", trimRange)}>
                  Export Trimmed Clip
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setTrimRange([0, 10])}
                >
                  Reset Trim
                </Button>
              </div>
            </div>
          )}

          {/* Comparison Mode */}
          {demoMode === "comparison" && (
            <div className="space-y-4">
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <h3 className="font-semibold text-purple-900 mb-2">
                  Comparison Mode:
                </h3>
                <ul className="text-sm text-purple-800 space-y-1">
                  <li>
                    1. All videos play in perfect sync
                  </li>
                  <li>
                    2. Compare different variations side-by-side
                  </li>
                  <li>
                    3. Ideal for reviewing subtitle placement, zoom levels, or
                    effects
                  </li>
                  <li>
                    4. Single timeline controls all videos simultaneously
                  </li>
                </ul>
              </div>

              <VideoPreview
                sources={comparisonVideos}
                comparisonMode={true}
                enableTrimming={enableTrimming}
                showFrameNumber={showFrameNumber}
                autoPlay={autoPlay}
                trimRange={enableTrimming ? trimRange : undefined}
                onTrimChange={handleTrimChange}
                onTimeUpdate={handleTimeUpdate}
                thumbnailInterval={1}
              />
            </div>
          )}

          {/* Mobile Mode */}
          {demoMode === "mobile" && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="font-semibold text-green-900 mb-2">
                  Mobile Optimization:
                </h3>
                <ul className="text-sm text-green-800 space-y-1">
                  <li>
                    1. Touch-friendly controls with larger hit areas
                  </li>
                  <li>
                    2. Volume slider moves to separate row on mobile
                  </li>
                  <li>
                    3. Responsive layout adapts to screen size
                  </li>
                  <li>
                    4. Keyboard shortcuts still work on tablets with keyboards
                  </li>
                </ul>
              </div>

              <div className="max-w-sm mx-auto border-4 border-gray-800 rounded-2xl overflow-hidden shadow-2xl">
                <VideoPreview
                  sources={singleVideo}
                  enableTrimming={enableTrimming}
                  showFrameNumber={showFrameNumber}
                  autoPlay={autoPlay}
                  trimRange={enableTrimming ? trimRange : undefined}
                  onTrimChange={handleTrimChange}
                  onTimeUpdate={handleTimeUpdate}
                  className="rounded-none"
                />
              </div>
            </div>
          )}
        </Card>

        {/* Features List */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Features</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h3 className="font-semibold text-sm text-gray-600 uppercase">
                Playback Controls
              </h3>
              <ul className="space-y-1 text-sm">
                <li>✓ Play/Pause</li>
                <li>✓ Skip forward/backward (10s)</li>
                <li>✓ Variable playback speed (0.25x - 2x)</li>
                <li>✓ Volume control with mute</li>
                <li>✓ Fullscreen mode</li>
              </ul>
            </div>

            <div className="space-y-2">
              <h3 className="font-semibold text-sm text-gray-600 uppercase">
                Timeline Features
              </h3>
              <ul className="space-y-1 text-sm">
                <li>✓ Click/drag to scrub</li>
                <li>✓ Thumbnail preview on hover</li>
                <li>✓ Buffered range indicator</li>
                <li>✓ Current time display</li>
                <li>✓ Time tooltip on hover</li>
              </ul>
            </div>

            <div className="space-y-2">
              <h3 className="font-semibold text-sm text-gray-600 uppercase">
                Advanced Features
              </h3>
              <ul className="space-y-1 text-sm">
                <li>✓ Frame-by-frame navigation</li>
                <li>✓ Frame number overlay</li>
                <li>✓ Trim adjustment handles</li>
                <li>✓ Side-by-side comparison</li>
                <li>✓ Synchronized multi-video playback</li>
              </ul>
            </div>

            <div className="space-y-2">
              <h3 className="font-semibold text-sm text-gray-600 uppercase">
                Keyboard Shortcuts
              </h3>
              <ul className="space-y-1 text-sm">
                <li>✓ Space: Play/Pause</li>
                <li>✓ ←/→: Skip 5 seconds</li>
                <li>✓ ,/.: Frame step</li>
                <li>✓ M: Toggle mute</li>
                <li>✓ F: Fullscreen</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* Keyboard Shortcuts Reference */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">
            Complete Keyboard Shortcuts
          </h2>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Play/Pause</span>
                <kbd className="px-2 py-1 bg-gray-100 rounded border">
                  Space
                </kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Skip backward 5s</span>
                <kbd className="px-2 py-1 bg-gray-100 rounded border">←</kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Skip forward 5s</span>
                <kbd className="px-2 py-1 bg-gray-100 rounded border">→</kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Previous frame</span>
                <kbd className="px-2 py-1 bg-gray-100 rounded border">,</kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Next frame</span>
                <kbd className="px-2 py-1 bg-gray-100 rounded border">.</kbd>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Volume up</span>
                <kbd className="px-2 py-1 bg-gray-100 rounded border">↑</kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Volume down</span>
                <kbd className="px-2 py-1 bg-gray-100 rounded border">↓</kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Toggle mute</span>
                <kbd className="px-2 py-1 bg-gray-100 rounded border">M</kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Toggle fullscreen</span>
                <kbd className="px-2 py-1 bg-gray-100 rounded border">F</kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Seek to start</span>
                <kbd className="px-2 py-1 bg-gray-100 rounded border">0</kbd>
              </div>
            </div>
          </div>
        </Card>

        {/* Usage Example */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Start Example</h2>
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
            {`import { VideoPreview } from "@/components/video-preview"

export function MyComponent() {
  return (
    <VideoPreview
      sources={{
        id: "my-clip",
        url: "http://localhost:8000/clips/my-clip.mp4"
      }}
      enableTrimming={true}
      showFrameNumber={true}
      onTrimChange={(start, end) => {
        console.log("Trim:", start, end)
      }}
    />
  )
}`}
          </pre>
        </Card>
      </div>
    </div>
  )
}

export default VideoPreviewDemo
