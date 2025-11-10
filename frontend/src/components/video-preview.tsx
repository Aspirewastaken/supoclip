"use client"

import React, { useRef, useState, useEffect, useCallback } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Maximize,
  Minimize,
  Volume2,
  VolumeX,
  ChevronLeft,
  ChevronRight,
  ScissorsIcon,
  Grid2X2,
  Maximize2,
} from "lucide-react"

export interface VideoSource {
  id: string
  url: string
  label?: string
  duration?: number
}

export interface VideoPreviewProps {
  /** Single video source or multiple sources for comparison */
  sources: VideoSource | VideoSource[]
  /** Optional trim range in seconds [start, end] */
  trimRange?: [number, number]
  /** Callback when trim range changes */
  onTrimChange?: (start: number, end: number) => void
  /** Enable trim adjustment handles */
  enableTrimming?: boolean
  /** Enable side-by-side comparison mode */
  comparisonMode?: boolean
  /** Thumbnail generation interval in seconds */
  thumbnailInterval?: number
  /** Custom className */
  className?: string
  /** Auto-play on mount */
  autoPlay?: boolean
  /** Show frame number overlay */
  showFrameNumber?: boolean
  /** Frames per second for frame-by-frame navigation */
  fps?: number
  /** Callback when playback time changes */
  onTimeUpdate?: (time: number) => void
}

interface VideoState {
  isPlaying: boolean
  currentTime: number
  duration: number
  volume: number
  isMuted: boolean
  playbackRate: number
  isFullscreen: boolean
  buffered: number
}

export function VideoPreview({
  sources,
  trimRange,
  onTrimChange,
  enableTrimming = false,
  comparisonMode = false,
  thumbnailInterval = 1,
  className,
  autoPlay = false,
  showFrameNumber = false,
  fps = 30,
  onTimeUpdate,
}: VideoPreviewProps) {
  // Normalize sources to array
  const videoSources = Array.isArray(sources) ? sources : [sources]
  const isComparison = comparisonMode && videoSources.length > 1

  // Video refs
  const videoRefs = useRef<(HTMLVideoElement | null)[]>([])
  const containerRef = useRef<HTMLDivElement>(null)
  const timelineRef = useRef<HTMLDivElement>(null)
  const isDragging = useRef(false)
  const isTrimDragging = useRef<"start" | "end" | null>(null)

  // State
  const [videoStates, setVideoStates] = useState<VideoState[]>(
    videoSources.map(() => ({
      isPlaying: false,
      currentTime: 0,
      duration: 0,
      volume: 1,
      isMuted: false,
      playbackRate: 1,
      isFullscreen: false,
      buffered: 0,
    }))
  )

  const [thumbnails, setThumbnails] = useState<string[]>([])
  const [localTrimRange, setLocalTrimRange] = useState<[number, number]>(
    trimRange || [0, 0]
  )
  const [hoveredTime, setHoveredTime] = useState<number | null>(null)

  // Sync all videos (for comparison mode)
  const primaryVideoState = videoStates[0]

  // Format time as MM:SS
  const formatTime = (seconds: number) => {
    if (!isFinite(seconds)) return "00:00"
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  // Get frame number from time
  const getFrameNumber = (time: number) => {
    return Math.floor(time * fps)
  }

  // Update video state for specific video
  const updateVideoState = useCallback(
    (index: number, updates: Partial<VideoState>) => {
      setVideoStates((prev) => {
        const newStates = [...prev]
        newStates[index] = { ...newStates[index], ...updates }
        return newStates
      })
    },
    []
  )

  // Sync all videos to primary video time
  const syncVideos = useCallback((time: number) => {
    videoRefs.current.forEach((video) => {
      if (video && Math.abs(video.currentTime - time) > 0.1) {
        video.currentTime = time
      }
    })
  }, [])

  // Play/Pause toggle
  const togglePlayPause = useCallback(() => {
    videoRefs.current.forEach((video, index) => {
      if (video) {
        if (video.paused) {
          video.play()
          updateVideoState(index, { isPlaying: true })
        } else {
          video.pause()
          updateVideoState(index, { isPlaying: false })
        }
      }
    })
  }, [updateVideoState])

  // Seek to specific time
  const seekTo = useCallback(
    (time: number) => {
      const clampedTime = Math.max(
        0,
        Math.min(time, primaryVideoState.duration)
      )
      syncVideos(clampedTime)
      videoStates.forEach((_, index) => {
        updateVideoState(index, { currentTime: clampedTime })
      })
      onTimeUpdate?.(clampedTime)
    },
    [primaryVideoState.duration, syncVideos, updateVideoState, videoStates, onTimeUpdate]
  )

  // Frame-by-frame navigation
  const seekByFrames = useCallback(
    (frames: number) => {
      const frameTime = 1 / fps
      const newTime = primaryVideoState.currentTime + frames * frameTime
      seekTo(newTime)
    },
    [fps, primaryVideoState.currentTime, seekTo]
  )

  // Skip forward/backward
  const skip = useCallback(
    (seconds: number) => {
      seekTo(primaryVideoState.currentTime + seconds)
    },
    [primaryVideoState.currentTime, seekTo]
  )

  // Toggle mute
  const toggleMute = useCallback(() => {
    videoRefs.current.forEach((video, index) => {
      if (video) {
        video.muted = !video.muted
        updateVideoState(index, { isMuted: video.muted })
      }
    })
  }, [updateVideoState])

  // Change volume
  const changeVolume = useCallback(
    (value: number[]) => {
      const volume = value[0]
      videoRefs.current.forEach((video, index) => {
        if (video) {
          video.volume = volume
          updateVideoState(index, { volume, isMuted: volume === 0 })
        }
      })
    },
    [updateVideoState]
  )

  // Change playback rate
  const changePlaybackRate = useCallback(
    (rate: number) => {
      videoRefs.current.forEach((video, index) => {
        if (video) {
          video.playbackRate = rate
          updateVideoState(index, { playbackRate: rate })
        }
      })
    },
    [updateVideoState]
  )

  // Toggle fullscreen
  const toggleFullscreen = useCallback(() => {
    if (!containerRef.current) return

    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen()
      updateVideoState(0, { isFullscreen: true })
    } else {
      document.exitFullscreen()
      updateVideoState(0, { isFullscreen: false })
    }
  }, [updateVideoState])

  // Handle timeline scrubbing
  const handleTimelineScrub = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!timelineRef.current) return

      const rect = timelineRef.current.getBoundingClientRect()
      const x = e.clientX - rect.left
      const percentage = Math.max(0, Math.min(1, x / rect.width))
      const time = percentage * primaryVideoState.duration

      if (isDragging.current) {
        seekTo(time)
      }
    },
    [primaryVideoState.duration, seekTo]
  )

  // Handle trim range adjustment
  const handleTrimDrag = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!timelineRef.current || !isTrimDragging.current) return

      const rect = timelineRef.current.getBoundingClientRect()
      const x = e.clientX - rect.left
      const percentage = Math.max(0, Math.min(1, x / rect.width))
      const time = percentage * primaryVideoState.duration

      setLocalTrimRange((prev) => {
        let newRange: [number, number]
        if (isTrimDragging.current === "start") {
          newRange = [Math.min(time, prev[1] - 0.5), prev[1]]
        } else {
          newRange = [prev[0], Math.max(time, prev[0] + 0.5)]
        }
        onTrimChange?.(newRange[0], newRange[1])
        return newRange
      })
    },
    [primaryVideoState.duration, onTrimChange]
  )

  // Handle hover on timeline
  const handleTimelineHover = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!timelineRef.current) return

      const rect = timelineRef.current.getBoundingClientRect()
      const x = e.clientX - rect.left
      const percentage = Math.max(0, Math.min(1, x / rect.width))
      const time = percentage * primaryVideoState.duration

      setHoveredTime(time)
    },
    [primaryVideoState.duration]
  )

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return
      }

      switch (e.key) {
        case " ":
          e.preventDefault()
          togglePlayPause()
          break
        case "ArrowLeft":
          e.preventDefault()
          if (e.shiftKey) {
            seekByFrames(-1)
          } else {
            skip(-5)
          }
          break
        case "ArrowRight":
          e.preventDefault()
          if (e.shiftKey) {
            seekByFrames(1)
          } else {
            skip(5)
          }
          break
        case "ArrowUp":
          e.preventDefault()
          changeVolume([Math.min(1, primaryVideoState.volume + 0.1)])
          break
        case "ArrowDown":
          e.preventDefault()
          changeVolume([Math.max(0, primaryVideoState.volume - 0.1)])
          break
        case "m":
          e.preventDefault()
          toggleMute()
          break
        case "f":
          e.preventDefault()
          toggleFullscreen()
          break
        case ",":
          e.preventDefault()
          seekByFrames(-1)
          break
        case ".":
          e.preventDefault()
          seekByFrames(1)
          break
        case "0":
          e.preventDefault()
          seekTo(0)
          break
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [
    togglePlayPause,
    skip,
    seekByFrames,
    changeVolume,
    primaryVideoState.volume,
    toggleMute,
    toggleFullscreen,
    seekTo,
  ])

  // Generate thumbnails
  useEffect(() => {
    const video = videoRefs.current[0]
    if (!video || !video.duration || thumbnailInterval <= 0) return

    const generateThumbnails = async () => {
      const canvas = document.createElement("canvas")
      const ctx = canvas.getContext("2d")
      if (!ctx) return

      const thumbs: string[] = []
      const count = Math.floor(video.duration / thumbnailInterval)

      for (let i = 0; i <= count; i++) {
        const time = i * thumbnailInterval
        video.currentTime = time

        await new Promise((resolve) => {
          video.onseeked = () => {
            canvas.width = video.videoWidth / 4
            canvas.height = video.videoHeight / 4
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
            thumbs.push(canvas.toDataURL("image/jpeg", 0.6))
            resolve(null)
          }
        })
      }

      setThumbnails(thumbs)
      video.currentTime = 0
    }

    generateThumbnails()
  }, [thumbnailInterval])

  // Initialize trim range
  useEffect(() => {
    if (primaryVideoState.duration > 0 && localTrimRange[1] === 0) {
      setLocalTrimRange([0, primaryVideoState.duration])
    }
  }, [primaryVideoState.duration, localTrimRange])

  // Sync external trim range changes
  useEffect(() => {
    if (trimRange) {
      setLocalTrimRange(trimRange)
    }
  }, [trimRange])

  // Enforce trim range during playback
  useEffect(() => {
    if (!enableTrimming) return

    const video = videoRefs.current[0]
    if (!video) return

    const handleTimeUpdate = () => {
      if (
        video.currentTime < localTrimRange[0] ||
        video.currentTime > localTrimRange[1]
      ) {
        video.currentTime = localTrimRange[0]
        video.pause()
        updateVideoState(0, { isPlaying: false, currentTime: localTrimRange[0] })
      }
    }

    video.addEventListener("timeupdate", handleTimeUpdate)
    return () => video.removeEventListener("timeupdate", handleTimeUpdate)
  }, [enableTrimming, localTrimRange, updateVideoState])

  // Cleanup fullscreen listener
  useEffect(() => {
    const handleFullscreenChange = () => {
      updateVideoState(0, { isFullscreen: !!document.fullscreenElement })
    }

    document.addEventListener("fullscreenchange", handleFullscreenChange)
    return () =>
      document.removeEventListener("fullscreenchange", handleFullscreenChange)
  }, [updateVideoState])

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative w-full bg-black rounded-lg overflow-hidden flex flex-col",
        primaryVideoState.isFullscreen && "fixed inset-0 z-50 rounded-none",
        className
      )}
    >
      {/* Video Container */}
      <div
        className={cn(
          "relative flex-1 flex items-center justify-center bg-black",
          isComparison ? "gap-1" : ""
        )}
      >
        {videoSources.map((source, index) => (
          <div
            key={source.id}
            className={cn(
              "relative h-full",
              isComparison ? "flex-1" : "w-full"
            )}
          >
            <video
              ref={(el) => {
                videoRefs.current[index] = el
              }}
              src={source.url}
              className="w-full h-full object-contain"
              autoPlay={autoPlay}
              onLoadedMetadata={(e) => {
                const video = e.currentTarget
                updateVideoState(index, {
                  duration: video.duration,
                  currentTime: video.currentTime,
                })
              }}
              onTimeUpdate={(e) => {
                const video = e.currentTarget
                updateVideoState(index, { currentTime: video.currentTime })
                if (index === 0) {
                  onTimeUpdate?.(video.currentTime)
                }
              }}
              onPlay={() => updateVideoState(index, { isPlaying: true })}
              onPause={() => updateVideoState(index, { isPlaying: false })}
              onProgress={(e) => {
                const video = e.currentTarget
                if (video.buffered.length > 0) {
                  const buffered =
                    video.buffered.end(video.buffered.length - 1) / video.duration
                  updateVideoState(index, { buffered })
                }
              }}
            />

            {/* Video Label (comparison mode) */}
            {isComparison && source.label && (
              <div className="absolute top-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                {source.label}
              </div>
            )}

            {/* Frame Number Overlay */}
            {showFrameNumber && index === 0 && (
              <div className="absolute top-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded font-mono">
                Frame: {getFrameNumber(videoStates[index].currentTime)}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Controls Container */}
      <div className="relative bg-gradient-to-t from-black/90 via-black/80 to-transparent p-4 space-y-3">
        {/* Timeline */}
        <div className="space-y-2">
          <div
            ref={timelineRef}
            className="relative h-16 bg-gray-800/50 rounded-lg overflow-hidden cursor-pointer group"
            onMouseDown={(e) => {
              isDragging.current = true
              handleTimelineScrub(e)
            }}
            onMouseMove={(e) => {
              handleTimelineScrub(e)
              handleTimelineHover(e)
            }}
            onMouseUp={() => {
              isDragging.current = false
            }}
            onMouseLeave={() => {
              isDragging.current = false
              setHoveredTime(null)
            }}
          >
            {/* Thumbnail Background */}
            {thumbnails.length > 0 && (
              <div className="absolute inset-0 flex">
                {thumbnails.map((thumb, idx) => (
                  <div
                    key={idx}
                    className="flex-1 h-full bg-cover bg-center opacity-30"
                    style={{ backgroundImage: `url(${thumb})` }}
                  />
                ))}
              </div>
            )}

            {/* Buffered Range */}
            <div
              className="absolute top-0 left-0 h-full bg-gray-600/30"
              style={{
                width: `${primaryVideoState.buffered * 100}%`,
              }}
            />

            {/* Trim Range Overlay */}
            {enableTrimming && (
              <>
                {/* Before trim start */}
                <div
                  className="absolute top-0 left-0 h-full bg-black/60"
                  style={{
                    width: `${(localTrimRange[0] / primaryVideoState.duration) * 100}%`,
                  }}
                />
                {/* After trim end */}
                <div
                  className="absolute top-0 h-full bg-black/60"
                  style={{
                    left: `${(localTrimRange[1] / primaryVideoState.duration) * 100}%`,
                    right: 0,
                  }}
                />

                {/* Trim Start Handle */}
                <div
                  className="absolute top-0 h-full w-1 bg-blue-500 cursor-ew-resize hover:w-2 transition-all z-10 group"
                  style={{
                    left: `${(localTrimRange[0] / primaryVideoState.duration) * 100}%`,
                  }}
                  onMouseDown={(e) => {
                    e.stopPropagation()
                    isTrimDragging.current = "start"
                  }}
                  onMouseMove={(e) => {
                    if (isTrimDragging.current) {
                      handleTrimDrag(e)
                    }
                  }}
                  onMouseUp={() => {
                    isTrimDragging.current = null
                  }}
                >
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-8 bg-blue-500 rounded-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <ScissorsIcon className="w-3 h-3 text-white" />
                  </div>
                </div>

                {/* Trim End Handle */}
                <div
                  className="absolute top-0 h-full w-1 bg-blue-500 cursor-ew-resize hover:w-2 transition-all z-10 group"
                  style={{
                    left: `${(localTrimRange[1] / primaryVideoState.duration) * 100}%`,
                  }}
                  onMouseDown={(e) => {
                    e.stopPropagation()
                    isTrimDragging.current = "end"
                  }}
                  onMouseMove={(e) => {
                    if (isTrimDragging.current) {
                      handleTrimDrag(e)
                    }
                  }}
                  onMouseUp={() => {
                    isTrimDragging.current = null
                  }}
                >
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-8 bg-blue-500 rounded-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <ScissorsIcon className="w-3 h-3 text-white" />
                  </div>
                </div>
              </>
            )}

            {/* Current Time Progress */}
            <div
              className="absolute top-0 left-0 h-full bg-blue-600/40 pointer-events-none"
              style={{
                width: `${(primaryVideoState.currentTime / primaryVideoState.duration) * 100}%`,
              }}
            />

            {/* Playhead */}
            <div
              className="absolute top-0 h-full w-0.5 bg-blue-500 pointer-events-none z-20"
              style={{
                left: `${(primaryVideoState.currentTime / primaryVideoState.duration) * 100}%`,
              }}
            >
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-white" />
            </div>

            {/* Hover Time Indicator */}
            {hoveredTime !== null && (
              <div
                className="absolute -top-8 -translate-x-1/2 bg-black/90 text-white text-xs px-2 py-1 rounded pointer-events-none"
                style={{
                  left: `${(hoveredTime / primaryVideoState.duration) * 100}%`,
                }}
              >
                {formatTime(hoveredTime)}
              </div>
            )}
          </div>

          {/* Time Display */}
          <div className="flex items-center justify-between text-white text-xs">
            <span className="font-mono">
              {formatTime(primaryVideoState.currentTime)}
            </span>
            {enableTrimming && (
              <span className="text-gray-400 text-xs">
                Trim: {formatTime(localTrimRange[0])} -{" "}
                {formatTime(localTrimRange[1])} (
                {formatTime(localTrimRange[1] - localTrimRange[0])})
              </span>
            )}
            <span className="font-mono">
              {formatTime(primaryVideoState.duration)}
            </span>
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex items-center gap-2 justify-between">
          {/* Left Controls */}
          <div className="flex items-center gap-2">
            {/* Play/Pause */}
            <Button
              variant="ghost"
              size="icon"
              onClick={togglePlayPause}
              className="text-white hover:bg-white/10"
            >
              {primaryVideoState.isPlaying ? (
                <Pause className="w-5 h-5" />
              ) : (
                <Play className="w-5 h-5" />
              )}
            </Button>

            {/* Skip Backward */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => skip(-10)}
              className="text-white hover:bg-white/10"
              title="Skip backward 10s"
            >
              <SkipBack className="w-4 h-4" />
            </Button>

            {/* Frame Backward */}
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => seekByFrames(-1)}
              className="text-white hover:bg-white/10"
              title="Previous frame (,)"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>

            {/* Frame Forward */}
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => seekByFrames(1)}
              className="text-white hover:bg-white/10"
              title="Next frame (.)"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>

            {/* Skip Forward */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => skip(10)}
              className="text-white hover:bg-white/10"
              title="Skip forward 10s"
            >
              <SkipForward className="w-4 h-4" />
            </Button>

            {/* Volume */}
            <div className="hidden sm:flex items-center gap-2 ml-2">
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={toggleMute}
                className="text-white hover:bg-white/10"
              >
                {primaryVideoState.isMuted || primaryVideoState.volume === 0 ? (
                  <VolumeX className="w-4 h-4" />
                ) : (
                  <Volume2 className="w-4 h-4" />
                )}
              </Button>
              <Slider
                value={[primaryVideoState.volume]}
                onValueChange={changeVolume}
                min={0}
                max={1}
                step={0.01}
                className="w-20"
              />
            </div>
          </div>

          {/* Right Controls */}
          <div className="flex items-center gap-2">
            {/* Playback Speed */}
            <select
              value={primaryVideoState.playbackRate}
              onChange={(e) => changePlaybackRate(Number(e.target.value))}
              className="bg-white/10 text-white text-xs px-2 py-1 rounded hover:bg-white/20 border-none outline-none"
            >
              <option value={0.25}>0.25x</option>
              <option value={0.5}>0.5x</option>
              <option value={0.75}>0.75x</option>
              <option value={1}>1x</option>
              <option value={1.25}>1.25x</option>
              <option value={1.5}>1.5x</option>
              <option value={2}>2x</option>
            </select>

            {/* Fullscreen */}
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={toggleFullscreen}
              className="text-white hover:bg-white/10"
            >
              {primaryVideoState.isFullscreen ? (
                <Minimize className="w-4 h-4" />
              ) : (
                <Maximize className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Mobile Volume Control */}
        <div className="sm:hidden flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={toggleMute}
            className="text-white hover:bg-white/10"
          >
            {primaryVideoState.isMuted || primaryVideoState.volume === 0 ? (
              <VolumeX className="w-4 h-4" />
            ) : (
              <Volume2 className="w-4 h-4" />
            )}
          </Button>
          <Slider
            value={[primaryVideoState.volume]}
            onValueChange={changeVolume}
            min={0}
            max={1}
            step={0.01}
            className="flex-1"
          />
        </div>

        {/* Keyboard Shortcuts Help */}
        <div className="hidden lg:block text-gray-400 text-xs space-y-1 border-t border-gray-700 pt-2 mt-2">
          <div className="flex gap-4">
            <span>
              <kbd className="px-1 py-0.5 bg-gray-700 rounded">Space</kbd> Play/Pause
            </span>
            <span>
              <kbd className="px-1 py-0.5 bg-gray-700 rounded">←/→</kbd> Skip 5s
            </span>
            <span>
              <kbd className="px-1 py-0.5 bg-gray-700 rounded">,/.</kbd> Frame Step
            </span>
            <span>
              <kbd className="px-1 py-0.5 bg-gray-700 rounded">M</kbd> Mute
            </span>
            <span>
              <kbd className="px-1 py-0.5 bg-gray-700 rounded">F</kbd> Fullscreen
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
