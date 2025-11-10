"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export type ProcessingState =
  | "queued"
  | "transcribing"
  | "analyzing"
  | "rendering"
  | "complete"
  | "error";

interface ProcessingAnimationProps {
  state: ProcessingState;
  progress?: number; // 0-100
  estimatedTime?: number; // in seconds
  className?: string;
  taskName?: string;
}

const stateConfig = {
  queued: {
    label: "Queued",
    color: "bg-slate-500",
    badgeVariant: "outline" as const,
    icon: "⏳",
    description: "Waiting to start...",
  },
  transcribing: {
    label: "Transcribing",
    color: "bg-blue-500",
    badgeVariant: "default" as const,
    icon: "🎙️",
    description: "Converting speech to text...",
  },
  analyzing: {
    label: "Analyzing",
    color: "bg-purple-500",
    badgeVariant: "default" as const,
    icon: "🧠",
    description: "Finding viral moments...",
  },
  rendering: {
    label: "Rendering",
    color: "bg-orange-500",
    badgeVariant: "default" as const,
    icon: "🎬",
    description: "Creating clips...",
  },
  complete: {
    label: "Complete",
    color: "bg-green-500",
    badgeVariant: "default" as const,
    icon: "✅",
    description: "All done!",
  },
  error: {
    label: "Error",
    color: "bg-red-500",
    badgeVariant: "destructive" as const,
    icon: "❌",
    description: "Something went wrong",
  },
};

function PixelatedSpinner({ color }: { color: string }) {
  return (
    <div className="relative w-16 h-16 pixel-art">
      <div className={cn("absolute inset-0 animate-spin", color)}>
        <div className="w-full h-full relative">
          {/* Pixelated spinner squares */}
          <div className={cn("absolute top-0 left-1/2 w-2 h-2 -translate-x-1/2", color)} />
          <div className={cn("absolute top-0 right-2 w-2 h-2", color, "opacity-90")} />
          <div className={cn("absolute top-1/2 right-0 w-2 h-2 -translate-y-1/2", color, "opacity-80")} />
          <div className={cn("absolute bottom-2 right-2 w-2 h-2", color, "opacity-70")} />
          <div className={cn("absolute bottom-0 left-1/2 w-2 h-2 -translate-x-1/2", color, "opacity-60")} />
          <div className={cn("absolute bottom-2 left-2 w-2 h-2", color, "opacity-70")} />
          <div className={cn("absolute top-1/2 left-0 w-2 h-2 -translate-y-1/2", color, "opacity-80")} />
          <div className={cn("absolute top-2 left-2 w-2 h-2", color, "opacity-90")} />
        </div>
      </div>
    </div>
  );
}

function PixelatedProgressBar({ progress, color }: { progress: number; color: string }) {
  const blocks = 20; // Number of pixel blocks
  const filledBlocks = Math.floor((progress / 100) * blocks);

  return (
    <div className="flex gap-1 items-center justify-center">
      {Array.from({ length: blocks }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "w-2 h-4 border border-current transition-all duration-200 pixel-art",
            i < filledBlocks ? cn(color, "opacity-100") : "bg-transparent opacity-20",
            i === filledBlocks - 1 && "animate-pulse"
          )}
        />
      ))}
    </div>
  );
}

function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}

function FloatingPixels({ color }: { color: string }) {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-30">
      {Array.from({ length: 8 }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "absolute w-1 h-1 pixel-art animate-float",
            color
          )}
          style={{
            left: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 3}s`,
            animationDuration: `${3 + Math.random() * 2}s`,
          }}
        />
      ))}
    </div>
  );
}

export function ProcessingAnimation({
  state,
  progress = 0,
  estimatedTime,
  className,
  taskName,
}: ProcessingAnimationProps) {
  const config = stateConfig[state];
  const isProcessing = ["transcribing", "analyzing", "rendering"].includes(state);
  const [dots, setDots] = React.useState("");

  // Animated dots for processing states
  React.useEffect(() => {
    if (!isProcessing) return;

    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 500);

    return () => clearInterval(interval);
  }, [isProcessing]);

  return (
    <Card className={cn("relative overflow-hidden", className)}>
      <style jsx global>{`
        .pixel-art {
          image-rendering: pixelated;
          image-rendering: -moz-crisp-edges;
          image-rendering: crisp-edges;
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(100vh) scale(0);
            opacity: 0;
          }
          10% {
            opacity: 1;
          }
          90% {
            opacity: 1;
          }
          100% {
            transform: translateY(-20px) scale(1);
            opacity: 0;
          }
        }

        .animate-float {
          animation: float 3s linear infinite;
        }

        @keyframes pixelate-pulse {
          0%, 100% {
            transform: scale(1);
            filter: contrast(1);
          }
          50% {
            transform: scale(1.05);
            filter: contrast(1.2);
          }
        }

        .pixelate-pulse {
          animation: pixelate-pulse 2s ease-in-out infinite;
        }

        @keyframes scan-line {
          0% {
            transform: translateY(-100%);
          }
          100% {
            transform: translateY(100%);
          }
        }

        .scan-line {
          animation: scan-line 3s linear infinite;
        }
      `}</style>

      <FloatingPixels color={config.color} />

      {/* Retro scan line effect */}
      {isProcessing && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="scan-line absolute inset-x-0 h-0.5 bg-white opacity-10" />
        </div>
      )}

      <CardContent className="relative z-10 flex flex-col items-center gap-6 py-8">
        {/* Icon and Spinner */}
        <div className="relative">
          {isProcessing ? (
            <PixelatedSpinner color={config.color} />
          ) : (
            <div
              className={cn(
                "w-16 h-16 flex items-center justify-center text-4xl pixel-art",
                state === "complete" && "pixelate-pulse"
              )}
            >
              {config.icon}
            </div>
          )}
        </div>

        {/* Status Badge */}
        <div className="flex flex-col items-center gap-2">
          <Badge variant={config.badgeVariant} className="text-sm font-bold pixel-art">
            {config.label}
            {isProcessing && <span className="inline-block w-4 text-left">{dots}</span>}
          </Badge>
          <p className="text-sm text-muted-foreground text-center pixel-art">
            {config.description}
          </p>
        </div>

        {/* Task Name */}
        {taskName && (
          <p className="text-xs text-muted-foreground font-mono truncate max-w-full px-4">
            {taskName}
          </p>
        )}

        {/* Progress Bar */}
        {state !== "queued" && state !== "error" && (
          <div className="w-full space-y-3">
            {/* Pixelated Progress Bar */}
            <PixelatedProgressBar progress={progress} color={config.color} />

            {/* Standard Progress Bar for fallback */}
            <Progress value={progress} className="h-2" />

            {/* Progress Percentage */}
            <div className="flex items-center justify-between text-sm">
              <span className="font-mono font-bold pixel-art">{Math.round(progress)}%</span>
              {estimatedTime !== undefined && estimatedTime > 0 && state !== "complete" && (
                <span className="text-muted-foreground font-mono pixel-art">
                  ~{formatTime(estimatedTime)} remaining
                </span>
              )}
            </div>
          </div>
        )}

        {/* Complete State Message */}
        {state === "complete" && (
          <div className="text-center space-y-1">
            <p className="text-sm font-medium text-green-600 dark:text-green-400 pixel-art">
              Processing complete!
            </p>
            <p className="text-xs text-muted-foreground">
              Your clips are ready to view
            </p>
          </div>
        )}

        {/* Error State Message */}
        {state === "error" && (
          <div className="text-center space-y-1">
            <p className="text-sm font-medium text-red-600 dark:text-red-400 pixel-art">
              Processing failed
            </p>
            <p className="text-xs text-muted-foreground">
              Please try again or contact support
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
