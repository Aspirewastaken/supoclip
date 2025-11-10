/**
 * Demo Page for SwipeControls Component
 *
 * To test this page:
 * 1. Start the backend: cd backend && uvicorn src.main:app --reload
 * 2. Start the frontend: cd frontend && npm run dev
 * 3. Navigate to: http://localhost:3000/clip-review-demo
 *
 * This page demonstrates the SwipeControls component with mock data.
 * Replace with actual API calls in production.
 */

"use client";

import { useState } from "react";
import SwipeControls, { Clip } from "@/components/swipe-controls";
import { toast } from "sonner";

// Mock clip data - replace with actual API data
const MOCK_CLIPS: Clip[] = [
  {
    id: "1",
    url: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    title: "Big Buck Bunny",
    duration: 30,
  },
  {
    id: "2",
    url: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
    title: "Elephants Dream",
    duration: 45,
  },
  {
    id: "3",
    url: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    title: "For Bigger Blazes",
    duration: 15,
  },
  {
    id: "4",
    url: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    title: "For Bigger Escapes",
    duration: 20,
  },
];

export default function ClipReviewDemoPage() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [rejected, setRejected] = useState<Set<string>>(new Set());

  const handleNavigate = (newIndex: number) => {
    setCurrentIndex(newIndex);
  };

  const handleFavorite = (clip: Clip) => {
    const newFavorites = new Set(favorites);

    if (newFavorites.has(clip.id)) {
      newFavorites.delete(clip.id);
      toast.info(`Removed "${clip.title}" from favorites`);
    } else {
      newFavorites.add(clip.id);
      // Remove from rejected if it was rejected
      const newRejected = new Set(rejected);
      newRejected.delete(clip.id);
      setRejected(newRejected);
      toast.success(`Added "${clip.title}" to favorites!`);
    }

    setFavorites(newFavorites);
  };

  const handleReject = (clip: Clip) => {
    const newRejected = new Set(rejected);

    if (newRejected.has(clip.id)) {
      newRejected.delete(clip.id);
      toast.info(`Unmarked "${clip.title}" as rejected`);
    } else {
      newRejected.add(clip.id);
      // Remove from favorites if it was favorited
      const newFavorites = new Set(favorites);
      newFavorites.delete(clip.id);
      setFavorites(newFavorites);
      toast.error(`Marked "${clip.title}" as rejected`);
    }

    setRejected(newRejected);
  };

  const renderClipContent = (clip: Clip, index: number) => {
    const isFavorite = favorites.has(clip.id);
    const isRejected = rejected.has(clip.id);

    return (
      <div className="space-y-4 p-4">
        {/* Status badges */}
        <div className="flex gap-2 justify-center">
          {isFavorite && (
            <span className="bg-red-500 text-white text-xs font-medium px-3 py-1 rounded-full">
              ❤️ Favorited
            </span>
          )}
          {isRejected && (
            <span className="bg-gray-500 text-white text-xs font-medium px-3 py-1 rounded-full">
              ✕ Rejected
            </span>
          )}
        </div>

        {/* Video player */}
        <div className="relative bg-black rounded-lg overflow-hidden max-w-md mx-auto">
          <video
            src={clip.url}
            controls
            autoPlay
            muted
            loop
            className="w-full h-auto"
            style={{ maxHeight: "70vh" }}
          />
        </div>

        {/* Clip metadata */}
        <div className="text-center space-y-2">
          <h3 className="font-semibold text-xl">{clip.title}</h3>
          {clip.duration && (
            <p className="text-sm text-gray-600">
              Duration: {clip.duration}s
            </p>
          )}
        </div>
      </div>
    );
  };

  const filteredClips = MOCK_CLIPS;
  const currentClip = filteredClips[currentIndex];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto py-8 max-w-5xl px-4">
        {/* Header */}
        <div className="mb-8 text-center space-y-2">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Clip Review Demo
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Use arrow keys, swipe gestures, or click buttons to navigate
          </p>
          <div className="flex gap-2 justify-center text-sm text-gray-500 flex-wrap">
            <kbd className="px-2 py-1 bg-white dark:bg-gray-800 rounded border">←</kbd>
            <kbd className="px-2 py-1 bg-white dark:bg-gray-800 rounded border">→</kbd>
            <span>Navigate</span>
            <span className="text-gray-300">|</span>
            <kbd className="px-2 py-1 bg-white dark:bg-gray-800 rounded border">F</kbd>
            <span>Favorite</span>
            <span className="text-gray-300">|</span>
            <kbd className="px-2 py-1 bg-white dark:bg-gray-800 rounded border">Del</kbd>
            <span>Reject</span>
          </div>
        </div>

        {/* SwipeControls Component */}
        <div className="mb-8">
          <SwipeControls
            clips={filteredClips}
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
        </div>

        {/* Summary Section */}
        <div className="mt-8 p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg space-y-6">
          <h2 className="text-2xl font-semibold text-center">Review Summary</h2>

          {/* Statistics */}
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {filteredClips.length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Clips</div>
            </div>
            <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div className="text-3xl font-bold text-red-600 dark:text-red-400">
                {favorites.size}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Favorites</div>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="text-3xl font-bold text-gray-600 dark:text-gray-400">
                {rejected.size}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Rejected</div>
            </div>
          </div>

          {/* Clip Lists */}
          <div className="grid md:grid-cols-2 gap-4">
            {/* Favorites List */}
            <div className="space-y-2">
              <h3 className="font-semibold flex items-center gap-2">
                <span className="text-red-500">❤️</span>
                Favorited Clips ({favorites.size})
              </h3>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {Array.from(favorites).length === 0 ? (
                  <p className="text-sm text-gray-500 italic">No favorites yet</p>
                ) : (
                  Array.from(favorites).map((id) => {
                    const clip = MOCK_CLIPS.find((c) => c.id === id);
                    return (
                      <div
                        key={id}
                        className="text-sm p-2 bg-red-50 dark:bg-red-900/20 rounded flex justify-between items-center"
                      >
                        <span>{clip?.title}</span>
                        <button
                          onClick={() => {
                            const index = MOCK_CLIPS.findIndex((c) => c.id === id);
                            setCurrentIndex(index);
                          }}
                          className="text-xs text-blue-600 hover:underline"
                        >
                          View
                        </button>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Rejected List */}
            <div className="space-y-2">
              <h3 className="font-semibold flex items-center gap-2">
                <span className="text-gray-500">✕</span>
                Rejected Clips ({rejected.size})
              </h3>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {Array.from(rejected).length === 0 ? (
                  <p className="text-sm text-gray-500 italic">No rejected clips</p>
                ) : (
                  Array.from(rejected).map((id) => {
                    const clip = MOCK_CLIPS.find((c) => c.id === id);
                    return (
                      <div
                        key={id}
                        className="text-sm p-2 bg-gray-50 dark:bg-gray-700 rounded flex justify-between items-center"
                      >
                        <span>{clip?.title}</span>
                        <button
                          onClick={() => {
                            const index = MOCK_CLIPS.findIndex((c) => c.id === id);
                            setCurrentIndex(index);
                          }}
                          className="text-xs text-blue-600 hover:underline"
                        >
                          View
                        </button>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 justify-center pt-4 border-t dark:border-gray-700">
            <button
              onClick={() => {
                console.log("Favorites:", Array.from(favorites));
                toast.success("Favorites saved to console");
              }}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              disabled={favorites.size === 0}
            >
              Export Favorites
            </button>
            <button
              onClick={() => {
                console.log("Rejected:", Array.from(rejected));
                toast.success("Rejected list saved to console");
              }}
              className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
              disabled={rejected.size === 0}
            >
              Export Rejected
            </button>
            <button
              onClick={() => {
                setFavorites(new Set());
                setRejected(new Set());
                toast.info("Reset all selections");
              }}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
            >
              Reset All
            </button>
          </div>
        </div>

        {/* Integration Instructions */}
        <div className="mt-8 p-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <h3 className="font-semibold mb-2">🚀 Integration Notes</h3>
          <ul className="text-sm space-y-1 text-gray-700 dark:text-gray-300">
            <li>• Replace MOCK_CLIPS with actual API data from backend</li>
            <li>• Use <code className="bg-white dark:bg-gray-800 px-1 rounded">fetch(`/tasks/{`{taskId}`}/clips`)</code> to load clips</li>
            <li>• Integrate with DynamicVideoPlayer for better video handling</li>
            <li>• Add authentication to save favorites/rejected to database</li>
            <li>• See /frontend/src/components/SWIPE_CONTROLS_README.md for full docs</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
