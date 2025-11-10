"use client";

import * as React from "react";
import { ProcessingAnimation, ProcessingState } from "./processing-animation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Example usage of the ProcessingAnimation component
 * This demonstrates all the different states and how to integrate with a task processing flow
 */
export function ProcessingAnimationExample() {
  const [state, setState] = React.useState<ProcessingState>("queued");
  const [progress, setProgress] = React.useState(0);
  const [estimatedTime, setEstimatedTime] = React.useState(120);

  // Simulate processing flow
  const startProcessing = () => {
    setState("queued");
    setProgress(0);
    setEstimatedTime(120);

    // Queue -> Transcribing
    setTimeout(() => {
      setState("transcribing");
      simulateProgress(0, 30, 3000, () => {
        // Transcribing -> Analyzing
        setState("analyzing");
        setEstimatedTime(80);
        simulateProgress(30, 60, 3000, () => {
          // Analyzing -> Rendering
          setState("rendering");
          setEstimatedTime(40);
          simulateProgress(60, 100, 4000, () => {
            // Rendering -> Complete
            setState("complete");
            setEstimatedTime(0);
          });
        });
      });
    }, 1000);
  };

  const simulateProgress = (
    start: number,
    end: number,
    duration: number,
    onComplete: () => void
  ) => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const percentage = Math.min(elapsed / duration, 1);
      const currentProgress = start + (end - start) * percentage;

      setProgress(currentProgress);
      setEstimatedTime(Math.max(0, ((duration - elapsed) / 1000)));

      if (percentage >= 1) {
        clearInterval(interval);
        onComplete();
      }
    }, 50);
  };

  const simulateError = () => {
    setState("transcribing");
    setProgress(15);
    setTimeout(() => {
      setState("error");
    }, 2000);
  };

  return (
    <div className="space-y-8 p-8 max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Processing Animation Demo</CardTitle>
          <CardDescription>
            Interactive demonstration of all processing states
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2 flex-wrap">
            <Button onClick={startProcessing}>Start Processing</Button>
            <Button onClick={simulateError} variant="destructive">
              Simulate Error
            </Button>
            <Button onClick={() => setState("queued")} variant="outline">
              Queued
            </Button>
            <Button onClick={() => setState("transcribing")} variant="outline">
              Transcribing
            </Button>
            <Button onClick={() => setState("analyzing")} variant="outline">
              Analyzing
            </Button>
            <Button onClick={() => setState("rendering")} variant="outline">
              Rendering
            </Button>
            <Button onClick={() => setState("complete")} variant="outline">
              Complete
            </Button>
          </div>
        </CardContent>
      </Card>

      <ProcessingAnimation
        state={state}
        progress={progress}
        estimatedTime={estimatedTime}
        taskName="my-awesome-video.mp4"
      />
    </div>
  );
}

/**
 * Basic usage examples
 */
export function BasicExamples() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-8">
      {/* Queued State */}
      <ProcessingAnimation
        state="queued"
        progress={0}
        taskName="video-1.mp4"
      />

      {/* Transcribing State */}
      <ProcessingAnimation
        state="transcribing"
        progress={25}
        estimatedTime={90}
        taskName="video-2.mp4"
      />

      {/* Analyzing State */}
      <ProcessingAnimation
        state="analyzing"
        progress={50}
        estimatedTime={60}
        taskName="video-3.mp4"
      />

      {/* Rendering State */}
      <ProcessingAnimation
        state="rendering"
        progress={75}
        estimatedTime={30}
        taskName="video-4.mp4"
      />

      {/* Complete State */}
      <ProcessingAnimation
        state="complete"
        progress={100}
        taskName="video-5.mp4"
      />

      {/* Error State */}
      <ProcessingAnimation
        state="error"
        progress={33}
        taskName="video-6.mp4"
      />
    </div>
  );
}

/**
 * Real-world integration example with SSE (Server-Sent Events)
 */
export function ProcessingWithSSE({ taskId }: { taskId: string }) {
  const [state, setState] = React.useState<ProcessingState>("queued");
  const [progress, setProgress] = React.useState(0);
  const [estimatedTime, setEstimatedTime] = React.useState<number | undefined>();

  React.useEffect(() => {
    // Connect to SSE endpoint for real-time updates
    const eventSource = new EventSource(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/tasks/${taskId}/progress`
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // Map backend status to component states
      const statusMap: Record<string, ProcessingState> = {
        pending: "queued",
        transcribing: "transcribing",
        analyzing: "analyzing",
        generating_clips: "rendering",
        completed: "complete",
        failed: "error",
      };

      setState(statusMap[data.status] || "queued");
      setProgress(data.progress || 0);
      setEstimatedTime(data.estimated_time);

      // Close connection when complete or failed
      if (data.status === "completed" || data.status === "failed") {
        eventSource.close();
      }
    };

    eventSource.onerror = () => {
      setState("error");
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [taskId]);

  return (
    <ProcessingAnimation
      state={state}
      progress={progress}
      estimatedTime={estimatedTime}
      taskName={`Task ${taskId}`}
    />
  );
}

/**
 * Minimal usage example
 */
export function MinimalExample() {
  return <ProcessingAnimation state="transcribing" progress={45} />;
}
