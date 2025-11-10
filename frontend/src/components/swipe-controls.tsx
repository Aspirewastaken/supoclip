"use client";

import React, { useEffect, useCallback, useState } from "react";
import { motion, AnimatePresence, PanInfo } from "framer-motion";
import { ChevronLeft, ChevronRight, Heart, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface Clip {
  id: string;
  url: string;
  [key: string]: any; // Allow additional clip properties
}

export interface SwipeControlsProps {
  clips: Clip[];
  currentIndex: number;
  onNavigate: (newIndex: number) => void;
  onFavorite?: (clip: Clip) => void;
  onReject?: (clip: Clip) => void;
  renderContent: (clip: Clip, index: number) => React.ReactNode;
  className?: string;
  showQuickActions?: boolean;
  swipeThreshold?: number;
  animationDuration?: number;
}

type SwipeDirection = "left" | "right" | null;

const SwipeControls: React.FC<SwipeControlsProps> = ({
  clips,
  currentIndex,
  onNavigate,
  onFavorite,
  onReject,
  renderContent,
  className = "",
  showQuickActions = true,
  swipeThreshold = 50,
  animationDuration = 0.3,
}) => {
  const [swipeDirection, setSwipeDirection] = useState<SwipeDirection>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Navigation handlers
  const goToPrevious = useCallback(() => {
    if (currentIndex > 0) {
      setSwipeDirection("right");
      setTimeout(() => {
        onNavigate(currentIndex - 1);
        setSwipeDirection(null);
      }, animationDuration * 1000);
    }
  }, [currentIndex, onNavigate, animationDuration]);

  const goToNext = useCallback(() => {
    if (currentIndex < clips.length - 1) {
      setSwipeDirection("left");
      setTimeout(() => {
        onNavigate(currentIndex + 1);
        setSwipeDirection(null);
      }, animationDuration * 1000);
    }
  }, [currentIndex, clips.length, onNavigate, animationDuration]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Prevent navigation when typing in input fields
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      switch (e.key) {
        case "ArrowLeft":
          e.preventDefault();
          goToPrevious();
          break;
        case "ArrowRight":
          e.preventDefault();
          goToNext();
          break;
        case "f":
        case "F":
          if (showQuickActions && onFavorite) {
            e.preventDefault();
            onFavorite(clips[currentIndex]);
          }
          break;
        case "Delete":
        case "Backspace":
          if (showQuickActions && onReject) {
            e.preventDefault();
            onReject(clips[currentIndex]);
          }
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentIndex, clips, goToPrevious, goToNext, onFavorite, onReject, showQuickActions]);

  // Swipe gesture handlers
  const handleDragStart = () => {
    setIsDragging(true);
  };

  const handleDragEnd = (
    event: MouseEvent | TouchEvent | PointerEvent,
    info: PanInfo
  ) => {
    setIsDragging(false);
    const swipeDistance = info.offset.x;

    if (Math.abs(swipeDistance) > swipeThreshold) {
      if (swipeDistance > 0) {
        // Swiped right, go to previous
        goToPrevious();
      } else {
        // Swiped left, go to next
        goToNext();
      }
    }
  };

  // Quick action handlers
  const handleFavorite = () => {
    if (onFavorite) {
      onFavorite(clips[currentIndex]);
    }
  };

  const handleReject = () => {
    if (onReject) {
      onReject(clips[currentIndex]);
    }
  };

  const canGoPrevious = currentIndex > 0;
  const canGoNext = currentIndex < clips.length - 1;

  // Animation variants
  const slideVariants = {
    enter: (direction: SwipeDirection) => ({
      x: direction === "left" ? 1000 : direction === "right" ? -1000 : 0,
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (direction: SwipeDirection) => ({
      x: direction === "left" ? -1000 : direction === "right" ? 1000 : 0,
      opacity: 0,
    }),
  };

  return (
    <div className={cn("relative w-full", className)}>
      {/* Counter Display */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 bg-black/70 backdrop-blur-sm px-4 py-2 rounded-full">
        <span className="text-white font-medium text-sm">
          {currentIndex + 1} / {clips.length}
        </span>
      </div>

      {/* Quick Actions */}
      {showQuickActions && (onFavorite || onReject) && (
        <div className="absolute top-4 right-4 z-20 flex gap-2">
          {onFavorite && (
            <Button
              variant="outline"
              size="icon"
              onClick={handleFavorite}
              className="bg-white/90 hover:bg-white border-0 shadow-lg"
              title="Favorite (F)"
            >
              <Heart className="size-5 text-red-500" />
            </Button>
          )}
          {onReject && (
            <Button
              variant="outline"
              size="icon"
              onClick={handleReject}
              className="bg-white/90 hover:bg-white border-0 shadow-lg"
              title="Reject (Delete)"
            >
              <X className="size-5 text-gray-700" />
            </Button>
          )}
        </div>
      )}

      {/* Main Content Area with Swipe Detection */}
      <div className="relative overflow-hidden">
        <AnimatePresence initial={false} custom={swipeDirection} mode="wait">
          <motion.div
            key={currentIndex}
            custom={swipeDirection}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{
              x: { type: "spring", stiffness: 300, damping: 30 },
              opacity: { duration: animationDuration },
            }}
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            dragElastic={0.2}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
            className={cn(
              "touch-pan-y",
              isDragging && "cursor-grabbing"
            )}
            style={{ cursor: isDragging ? "grabbing" : "grab" }}
          >
            {renderContent(clips[currentIndex], currentIndex)}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation Arrows */}
      <div className="absolute inset-y-0 left-0 right-0 flex items-center justify-between pointer-events-none z-10 px-4">
        {/* Left Arrow */}
        <Button
          variant="outline"
          size="icon-lg"
          onClick={goToPrevious}
          disabled={!canGoPrevious}
          className={cn(
            "pointer-events-auto bg-white/90 hover:bg-white border-0 shadow-xl transition-all",
            !canGoPrevious && "opacity-0 cursor-not-allowed"
          )}
          title="Previous (Arrow Left)"
        >
          <ChevronLeft className="size-6" />
        </Button>

        {/* Right Arrow */}
        <Button
          variant="outline"
          size="icon-lg"
          onClick={goToNext}
          disabled={!canGoNext}
          className={cn(
            "pointer-events-auto bg-white/90 hover:bg-white border-0 shadow-xl transition-all",
            !canGoNext && "opacity-0 cursor-not-allowed"
          )}
          title="Next (Arrow Right)"
        >
          <ChevronRight className="size-6" />
        </Button>
      </div>

      {/* Progress Indicators (optional dots) */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 flex gap-2">
        {clips.map((_, index) => (
          <button
            key={index}
            onClick={() => onNavigate(index)}
            className={cn(
              "size-2 rounded-full transition-all duration-300",
              index === currentIndex
                ? "bg-white w-8"
                : "bg-white/50 hover:bg-white/75"
            )}
            aria-label={`Go to clip ${index + 1}`}
          />
        ))}
      </div>

      {/* Swipe Hint (shown on first load) */}
      {currentIndex === 0 && clips.length > 1 && (
        <motion.div
          initial={{ opacity: 1 }}
          animate={{ opacity: 0 }}
          transition={{ delay: 2, duration: 1 }}
          className="absolute bottom-20 left-1/2 -translate-x-1/2 z-20 pointer-events-none"
        >
          <div className="bg-black/70 backdrop-blur-sm px-4 py-2 rounded-full">
            <span className="text-white text-sm flex items-center gap-2">
              <ChevronLeft className="size-4" />
              Swipe or use arrow keys
              <ChevronRight className="size-4" />
            </span>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default SwipeControls;
