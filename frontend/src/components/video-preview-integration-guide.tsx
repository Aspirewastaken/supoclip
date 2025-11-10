/**
 * VIDEO PREVIEW COMPONENT - INTEGRATION GUIDE
 *
 * This guide demonstrates how to use the VideoPreview component in your application.
 * The component provides a full-featured video player with timeline scrubbing,
 * frame-by-frame navigation, trim controls, and comparison mode.
 */

import { VideoPreview, type VideoSource } from "./video-preview"

// ============================================================================
// EXAMPLE 1: Basic Single Video Preview
// ============================================================================

export function BasicVideoPreviewExample() {
  const videoSource: VideoSource = {
    id: "clip-1",
    url: "http://localhost:8000/clips/example-clip-1.mp4",
    label: "Example Clip",
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      <h2 className="text-2xl font-bold mb-4">Basic Video Preview</h2>
      <VideoPreview sources={videoSource} autoPlay={false} />
    </div>
  )
}

// ============================================================================
// EXAMPLE 2: Video Preview with Trimming
// ============================================================================

export function VideoPreviewWithTrimmingExample() {
  const [trimRange, setTrimRange] = React.useState<[number, number]>([5, 15])

  const videoSource: VideoSource = {
    id: "clip-2",
    url: "http://localhost:8000/clips/example-clip-2.mp4",
  }

  const handleTrimChange = (start: number, end: number) => {
    console.log("Trim range changed:", { start, end })
    setTrimRange([start, end])
  }

  const handleExport = async () => {
    // Send trim range to backend for processing
    const response = await fetch("http://localhost:8000/clips/trim", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        clip_id: videoSource.id,
        start_time: trimRange[0],
        end_time: trimRange[1],
      }),
    })

    const result = await response.json()
    console.log("Trimmed clip:", result)
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-4 space-y-4">
      <h2 className="text-2xl font-bold">Video Trimming</h2>

      <VideoPreview
        sources={videoSource}
        trimRange={trimRange}
        onTrimChange={handleTrimChange}
        enableTrimming={true}
        showFrameNumber={true}
      />

      <div className="flex gap-2">
        <button
          onClick={handleExport}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Export Trimmed Clip
        </button>
        <button
          onClick={() => setTrimRange([0, 30])}
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
        >
          Reset Trim
        </button>
      </div>
    </div>
  )
}

// ============================================================================
// EXAMPLE 3: Side-by-Side Comparison Mode
// ============================================================================

export function VideoComparisonExample() {
  const videoSources: VideoSource[] = [
    {
      id: "original",
      url: "http://localhost:8000/clips/original-clip.mp4",
      label: "Original",
    },
    {
      id: "variation-1",
      url: "http://localhost:8000/clips/variation-1.mp4",
      label: "With Subtitles",
    },
    {
      id: "variation-2",
      url: "http://localhost:8000/clips/variation-2.mp4",
      label: "Zoomed",
    },
  ]

  return (
    <div className="w-full max-w-6xl mx-auto p-4">
      <h2 className="text-2xl font-bold mb-4">Compare Video Variations</h2>

      <VideoPreview
        sources={videoSources}
        comparisonMode={true}
        autoPlay={false}
      />

      <div className="mt-4 text-sm text-gray-600">
        All videos are synchronized. Use playback controls to compare variations
        side-by-side.
      </div>
    </div>
  )
}

// ============================================================================
// EXAMPLE 4: Integration with Task Detail Page
// ============================================================================

export function TaskDetailVideoPreview({ taskId }: { taskId: string }) {
  const [clips, setClips] = React.useState<any[]>([])
  const [selectedClip, setSelectedClip] = React.useState<any>(null)
  const [loading, setLoading] = React.useState(true)

  React.useEffect(() => {
    // Fetch clips for task
    const fetchClips = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/tasks/${taskId}/clips`
        )
        const data = await response.json()
        setClips(data.clips || [])
        if (data.clips?.length > 0) {
          setSelectedClip(data.clips[0])
        }
      } catch (error) {
        console.error("Failed to fetch clips:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchClips()
  }, [taskId])

  if (loading) {
    return <div>Loading clips...</div>
  }

  if (clips.length === 0) {
    return <div>No clips found</div>
  }

  const videoSource: VideoSource = {
    id: selectedClip.id,
    url: `http://localhost:8000/clips/${selectedClip.filename}`,
    label: selectedClip.title || `Clip ${selectedClip.segment_index + 1}`,
  }

  return (
    <div className="space-y-4">
      {/* Clip Selector */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {clips.map((clip) => (
          <button
            key={clip.id}
            onClick={() => setSelectedClip(clip)}
            className={`px-4 py-2 rounded whitespace-nowrap ${
              selectedClip?.id === clip.id
                ? "bg-blue-600 text-white"
                : "bg-gray-200 hover:bg-gray-300"
            }`}
          >
            Clip {clip.segment_index + 1}
          </button>
        ))}
      </div>

      {/* Video Preview */}
      <VideoPreview
        sources={videoSource}
        enableTrimming={true}
        showFrameNumber={true}
        thumbnailInterval={2}
        onTimeUpdate={(time) => {
          console.log("Current time:", time)
        }}
      />

      {/* Clip Metadata */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="font-semibold">Duration:</span>{" "}
          {selectedClip.duration?.toFixed(2)}s
        </div>
        <div>
          <span className="font-semibold">Timeframe:</span>{" "}
          {selectedClip.start_time?.toFixed(1)}s -{" "}
          {selectedClip.end_time?.toFixed(1)}s
        </div>
        <div className="col-span-2">
          <span className="font-semibold">Transcript:</span>
          <p className="mt-1 text-gray-600">{selectedClip.transcript_text}</p>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// EXAMPLE 5: Advanced - Multi-Clip Editor
// ============================================================================

export function MultiClipEditor({ clips }: { clips: any[] }) {
  const [selectedClips, setSelectedClips] = React.useState<string[]>([])
  const [currentClip, setCurrentClip] = React.useState<any>(clips[0])
  const [trimRanges, setTrimRanges] = React.useState<
    Record<string, [number, number]>
  >({})

  const handleTrimChange = (clipId: string, start: number, end: number) => {
    setTrimRanges((prev) => ({
      ...prev,
      [clipId]: [start, end],
    }))
  }

  const handleExportSequence = async () => {
    // Prepare sequence data for backend
    const sequence = selectedClips.map((clipId) => {
      const clip = clips.find((c) => c.id === clipId)
      const trimRange = trimRanges[clipId]

      return {
        clip_id: clipId,
        filename: clip.filename,
        start_time: trimRange?.[0] || clip.start_time,
        end_time: trimRange?.[1] || clip.end_time,
      }
    })

    console.log("Exporting sequence:", sequence)

    // Send to backend for processing
    const response = await fetch("http://localhost:8000/clips/merge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ clips: sequence }),
    })

    const result = await response.json()
    console.log("Merged video:", result)
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Multi-Clip Editor</h2>

      {/* Clip Library */}
      <div className="border rounded-lg p-4">
        <h3 className="font-semibold mb-2">Available Clips</h3>
        <div className="grid grid-cols-3 gap-2">
          {clips.map((clip) => (
            <button
              key={clip.id}
              onClick={() => setCurrentClip(clip)}
              className={`p-2 border rounded text-sm ${
                currentClip?.id === clip.id
                  ? "border-blue-600 bg-blue-50"
                  : "border-gray-300 hover:border-gray-400"
              }`}
            >
              Clip {clip.segment_index + 1}
            </button>
          ))}
        </div>
      </div>

      {/* Video Preview */}
      <VideoPreview
        sources={{
          id: currentClip.id,
          url: `http://localhost:8000/clips/${currentClip.filename}`,
        }}
        trimRange={trimRanges[currentClip.id]}
        onTrimChange={(start, end) =>
          handleTrimChange(currentClip.id, start, end)
        }
        enableTrimming={true}
        showFrameNumber={true}
        fps={30}
      />

      {/* Selected Clips Timeline */}
      <div className="border rounded-lg p-4">
        <h3 className="font-semibold mb-2">Sequence Timeline</h3>
        <div className="flex gap-2 min-h-16 items-center">
          {selectedClips.length === 0 ? (
            <p className="text-gray-400 text-sm">
              No clips selected. Click "Add to Sequence" below.
            </p>
          ) : (
            selectedClips.map((clipId, index) => {
              const clip = clips.find((c) => c.id === clipId)
              return (
                <div
                  key={index}
                  className="bg-blue-100 border border-blue-300 rounded px-3 py-2 text-sm"
                >
                  Clip {clip.segment_index + 1}
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() =>
            setSelectedClips((prev) => [...prev, currentClip.id])
          }
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Add to Sequence
        </button>
        <button
          onClick={handleExportSequence}
          disabled={selectedClips.length === 0}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Export Sequence ({selectedClips.length} clips)
        </button>
        <button
          onClick={() => setSelectedClips([])}
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
        >
          Clear Sequence
        </button>
      </div>
    </div>
  )
}

// ============================================================================
// EXAMPLE 6: Mobile-Optimized Preview
// ============================================================================

export function MobileVideoPreview({ clipUrl }: { clipUrl: string }) {
  return (
    <div className="w-full min-h-screen bg-black flex flex-col">
      <VideoPreview
        sources={{
          id: "mobile-clip",
          url: clipUrl,
        }}
        className="flex-1"
        autoPlay={false}
        thumbnailInterval={0.5}
      />

      <div className="p-4 bg-gray-900 text-white space-y-4">
        <h3 className="font-semibold">Quick Actions</h3>
        <div className="grid grid-cols-2 gap-2">
          <button className="px-4 py-3 bg-blue-600 rounded-lg hover:bg-blue-700">
            Download
          </button>
          <button className="px-4 py-3 bg-green-600 rounded-lg hover:bg-green-700">
            Share
          </button>
          <button className="px-4 py-3 bg-purple-600 rounded-lg hover:bg-purple-700">
            Edit
          </button>
          <button className="px-4 py-3 bg-red-600 rounded-lg hover:bg-red-700">
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// USAGE IN NEXT.JS APP ROUTER
// ============================================================================

/**
 * Example integration in app/tasks/[id]/page.tsx:
 *
 * ```tsx
 * import { VideoPreview } from "@/components/video-preview"
 *
 * export default async function TaskDetailPage({ params }: { params: { id: string } }) {
 *   const task = await getTask(params.id)
 *   const clips = await getTaskClips(params.id)
 *
 *   return (
 *     <div className="container mx-auto p-4">
 *       <h1>{task.title}</h1>
 *
 *       {clips.map((clip) => (
 *         <VideoPreview
 *           key={clip.id}
 *           sources={{
 *             id: clip.id,
 *             url: `${process.env.NEXT_PUBLIC_API_URL}/clips/${clip.filename}`,
 *           }}
 *           enableTrimming={true}
 *           showFrameNumber={true}
 *         />
 *       ))}
 *     </div>
 *   )
 * }
 * ```
 */

// ============================================================================
// KEYBOARD SHORTCUTS REFERENCE
// ============================================================================

/**
 * KEYBOARD SHORTCUTS:
 *
 * - Space: Play/Pause
 * - Arrow Left: Skip backward 5 seconds
 * - Arrow Right: Skip forward 5 seconds
 * - Shift + Arrow Left: Previous frame
 * - Shift + Arrow Right: Next frame
 * - , (comma): Previous frame
 * - . (period): Next frame
 * - Arrow Up: Increase volume
 * - Arrow Down: Decrease volume
 * - M: Toggle mute
 * - F: Toggle fullscreen
 * - 0: Seek to start
 */

// ============================================================================
// PROPS REFERENCE
// ============================================================================

/**
 * VideoPreview Component Props:
 *
 * @param sources - Single VideoSource or array for comparison mode
 * @param trimRange - Optional [start, end] in seconds
 * @param onTrimChange - Callback when trim range changes
 * @param enableTrimming - Show trim handles
 * @param comparisonMode - Enable side-by-side comparison
 * @param thumbnailInterval - Generate thumbnails every N seconds
 * @param className - Additional CSS classes
 * @param autoPlay - Auto-play on mount
 * @param showFrameNumber - Display current frame number
 * @param fps - Frames per second for frame navigation
 * @param onTimeUpdate - Callback on time change
 */

/**
 * VideoSource Type:
 *
 * interface VideoSource {
 *   id: string           // Unique identifier
 *   url: string          // Video URL
 *   label?: string       // Display label (for comparison mode)
 *   duration?: number    // Duration in seconds (optional)
 * }
 */
