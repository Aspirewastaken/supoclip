"use client";

/**
 * SwipeControls Integration Example
 *
 * This file demonstrates how to integrate the SwipeControls component
 * with video clips in your application.
 */

import React, { useState } from "react";
import SwipeControls, { Clip } from "./swipe-controls";
import DynamicVideoPlayer from "./dynamic-video-player";
import { toast } from "sonner";

interface ClipReviewProps {
  clips: Clip[];
}

export default function ClipReviewExample({ clips }: ClipReviewProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [rejected, setRejected] = useState<Set<string>>(new Set());

  // Navigation handler
  const handleNavigate = (newIndex: number) => {
    setCurrentIndex(newIndex);
  };

  // Favorite handler
  const handleFavorite = (clip: Clip) => {
    const newFavorites = new Set(favorites);

    if (newFavorites.has(clip.id)) {
      newFavorites.delete(clip.id);
      toast.info("Removed from favorites");
    } else {
      newFavorites.add(clip.id);
      // Remove from rejected if it was rejected
      const newRejected = new Set(rejected);
      newRejected.delete(clip.id);
      setRejected(newRejected);
      toast.success("Added to favorites!");
    }

    setFavorites(newFavorites);
  };

  // Reject handler
  const handleReject = (clip: Clip) => {
    const newRejected = new Set(rejected);

    if (newRejected.has(clip.id)) {
      newRejected.delete(clip.id);
      toast.info("Unmarked as rejected");
    } else {
      newRejected.add(clip.id);
      // Remove from favorites if it was favorited
      const newFavorites = new Set(favorites);
      newFavorites.delete(clip.id);
      setFavorites(newFavorites);
      toast.error("Marked as rejected");
    }

    setRejected(newRejected);
  };

  // Render clip content (video player)
  const renderClipContent = (clip: Clip, index: number) => {
    const isFavorite = favorites.has(clip.id);
    const isRejected = rejected.has(clip.id);

    return (
      <div className="space-y-4">
        {/* Status badges */}
        <div className="flex gap-2 justify-center">
          {isFavorite && (
            <span className="bg-red-500 text-white text-xs font-medium px-3 py-1 rounded-full">
              Favorited
            </span>
          )}
          {isRejected && (
            <span className="bg-gray-500 text-white text-xs font-medium px-3 py-1 rounded-full">
              Rejected
            </span>
          )}
        </div>

        {/* Video player */}
        <DynamicVideoPlayer
          src={clip.url}
          autoPlay={true}
          muted={true}
          loop={true}
          className="mx-auto"
        />

        {/* Clip metadata */}
        {clip.title && (
          <div className="text-center">
            <h3 className="font-semibold text-lg">{clip.title}</h3>
          </div>
        )}
        {clip.duration && (
          <div className="text-center text-sm text-gray-600">
            Duration: {clip.duration}s
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="container mx-auto py-8 max-w-4xl">
      <div className="mb-6 text-center">
        <h1 className="text-3xl font-bold mb-2">Clip Review</h1>
        <p className="text-gray-600">
          Use arrow keys, swipe, or click buttons to navigate
        </p>
      </div>

      {/* SwipeControls component */}
      <SwipeControls
        clips={clips}
        currentIndex={currentIndex}
        onNavigate={handleNavigate}
        onFavorite={handleFavorite}
        onReject={handleReject}
        renderContent={renderClipContent}
        showQuickActions={true}
        swipeThreshold={50}
        animationDuration={0.3}
        className="mb-8"
      />

      {/* Summary section */}
      <div className="mt-8 p-6 bg-gray-50 rounded-lg space-y-4">
        <h2 className="text-xl font-semibold">Review Summary</h2>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-3xl font-bold text-blue-600">{clips.length}</div>
            <div className="text-sm text-gray-600">Total Clips</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-red-600">{favorites.size}</div>
            <div className="text-sm text-gray-600">Favorites</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-gray-600">{rejected.size}</div>
            <div className="text-sm text-gray-600">Rejected</div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-4 justify-center pt-4">
          <button
            onClick={() => {
              console.log("Favorites:", Array.from(favorites));
              toast.success("Saved favorites to console");
            }}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Save Favorites
          </button>
          <button
            onClick={() => {
              console.log("Rejected:", Array.from(rejected));
              toast.success("Saved rejected to console");
            }}
            className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Save Rejected
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * BASIC USAGE EXAMPLE:
 *
 * import SwipeControls from "@/components/swipe-controls";
 *
 * const clips = [
 *   { id: "1", url: "http://localhost:8000/clips/clip1.mp4" },
 *   { id: "2", url: "http://localhost:8000/clips/clip2.mp4" },
 *   { id: "3", url: "http://localhost:8000/clips/clip3.mp4" },
 * ];
 *
 * function MyComponent() {
 *   const [currentIndex, setCurrentIndex] = useState(0);
 *
 *   return (
 *     <SwipeControls
 *       clips={clips}
 *       currentIndex={currentIndex}
 *       onNavigate={setCurrentIndex}
 *       renderContent={(clip) => (
 *         <video src={clip.url} controls />
 *       )}
 *     />
 *   );
 * }
 *
 * ADVANCED USAGE WITH ALL OPTIONS:
 *
 * <SwipeControls
 *   clips={clips}
 *   currentIndex={currentIndex}
 *   onNavigate={handleNavigate}
 *   onFavorite={handleFavorite}
 *   onReject={handleReject}
 *   renderContent={renderClipContent}
 *   className="my-custom-class"
 *   showQuickActions={true}
 *   swipeThreshold={50}
 *   animationDuration={0.3}
 * />
 *
 * KEYBOARD SHORTCUTS:
 * - Arrow Left/Right: Navigate between clips
 * - F: Favorite current clip
 * - Delete/Backspace: Reject current clip
 *
 * TOUCH/MOUSE GESTURES:
 * - Swipe left: Next clip
 * - Swipe right: Previous clip
 * - Click arrows: Navigate
 * - Click dots: Jump to specific clip
 */
