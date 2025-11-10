"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useSession } from "@/lib/auth-client";
import {
  ArrowLeft,
  Youtube,
  Upload,
  Loader2,
  CheckCircle,
  AlertCircle,
  Download,
  Film,
  FileText,
  Grid3x3,
  Play
} from "lucide-react";
import Link from "next/link";
import DynamicVideoPlayer from "@/components/dynamic-video-player";

interface MatrixOptions {
  enable_watermark: boolean;
  enable_title_card: boolean;
  enable_music: boolean;
  enable_captions: boolean;
  title_style: "tt3" | "adlab_standard";
  canvas_styles: string[];
}

interface Variation {
  id: string;
  filename: string;
  file_path: string;
  video_url: string;
  variation_type: string;
  temporal_variation: string;
  canvas_variation: string;
  clip_order: number;
}

interface ProgressData {
  progress: number;
  message: string;
  status: string;
}

export default function MatrixPage() {
  const router = useRouter();
  const { data: session } = useSession();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Form state
  const [sourceType, setSourceType] = useState<"youtube" | "upload">("upload");
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [userNotes, setUserNotes] = useState("");

  // Matrix options state
  const [matrixOptions, setMatrixOptions] = useState<MatrixOptions>({
    enable_watermark: true,
    enable_title_card: true,
    enable_music: true,
    enable_captions: true,
    title_style: "tt3",
    canvas_styles: ["original", "flipped", "blurry_bg"]
  });

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState("");
  const [status, setStatus] = useState<string>("idle");
  const [error, setError] = useState<string | null>(null);

  // Results state
  const [variations, setVariations] = useState<Variation[]>([]);
  const [selectedVariation, setSelectedVariation] = useState<Variation | null>(null);

  // Canvas style options
  const canvasStyleOptions = [
    { value: "original", label: "Original" },
    { value: "flipped", label: "Flipped" },
    { value: "blurry_bg", label: "Blurry Background" }
  ];

  // Handle canvas style toggle
  const toggleCanvasStyle = (style: string) => {
    setMatrixOptions(prev => ({
      ...prev,
      canvas_styles: prev.canvas_styles.includes(style)
        ? prev.canvas_styles.filter(s => s !== style)
        : [...prev.canvas_styles, style]
    }));
  };

  // Handle file upload to backend
  const handleFileUpload = async (file: File): Promise<string> => {
    const formData = new FormData();
    formData.append("video", file);

    const response = await fetch(`${apiUrl}/upload`, {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`);
    }

    const result = await response.json();
    return result.video_path;
  };

  // Start matrix generation
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!session?.user?.id) {
      setError("You must be logged in to generate clips");
      return;
    }

    if (sourceType === "youtube" && !youtubeUrl.trim()) {
      setError("Please enter a YouTube URL");
      return;
    }

    if (sourceType === "upload" && !uploadedFile) {
      setError("Please select a video file");
      return;
    }

    if (matrixOptions.canvas_styles.length === 0) {
      setError("Please select at least one canvas style");
      return;
    }

    try {
      setIsProcessing(true);
      setProgress(0);
      setProgressMessage("Starting matrix generation...");
      setStatus("starting");

      // Upload file if needed
      let videoPath = youtubeUrl;
      if (sourceType === "upload" && uploadedFile) {
        setProgressMessage("Uploading video file...");
        videoPath = await handleFileUpload(uploadedFile);
      }

      // Start matrix generation
      const response = await fetch(`${apiUrl}/mass/generate-matrix`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "user_id": session.user.id
        },
        body: JSON.stringify({
          uploaded_file_path: videoPath,
          source_type: sourceType,
          user_notes: userNotes,
          matrix_options: matrixOptions
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to start matrix generation");
      }

      const result = await response.json();
      setTaskId(result.task_id);
      setStatus("queued");
      setProgressMessage(result.message);

      // Connect to SSE for progress updates
      connectToProgressStream(result.task_id);

    } catch (err) {
      console.error("Error starting matrix generation:", err);
      setError(err instanceof Error ? err.message : "Failed to start generation");
      setIsProcessing(false);
    }
  };

  // Connect to SSE for real-time progress
  const connectToProgressStream = (taskId: string) => {
    const eventSource = new EventSource(`${apiUrl}/mass/status/${taskId}/stream`);

    eventSource.onmessage = (event) => {
      const data: ProgressData = JSON.parse(event.data);
      setProgress(data.progress);
      setProgressMessage(data.message);
      setStatus(data.status);

      // If completed, fetch results
      if (data.status === "completed") {
        eventSource.close();
        fetchResults(taskId);
      }

      // If error, close connection
      if (data.status === "error") {
        eventSource.close();
        setError(data.message || "An error occurred during processing");
        setIsProcessing(false);
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE error:", error);
      eventSource.close();

      // Don't set error immediately - might just be reconnecting
      // Instead, poll for status
      pollTaskStatus(taskId);
    };
  };

  // Fallback polling if SSE fails
  const pollTaskStatus = async (taskId: string) => {
    const maxAttempts = 10;
    let attempts = 0;

    const poll = async () => {
      if (attempts >= maxAttempts) {
        setError("Connection lost. Please refresh the page.");
        setIsProcessing(false);
        return;
      }

      try {
        const response = await fetch(`${apiUrl}/mass/status/${taskId}`, {
          headers: {
            "user_id": session?.user?.id || ""
          }
        });

        if (response.ok) {
          const data = await response.json();
          setProgress(data.progress);
          setProgressMessage(data.message);
          setStatus(data.status);

          if (data.status === "completed") {
            fetchResults(taskId);
            return;
          }

          if (data.status === "error") {
            setError("Processing failed");
            setIsProcessing(false);
            return;
          }

          // Continue polling
          setTimeout(poll, 2000);
          attempts++;
        }
      } catch (err) {
        console.error("Polling error:", err);
        attempts++;
        setTimeout(poll, 2000);
      }
    };

    poll();
  };

  // Fetch results when complete
  const fetchResults = async (taskId: string) => {
    try {
      const response = await fetch(`${apiUrl}/tasks/${taskId}/clips`, {
        headers: {
          "user_id": session?.user?.id || ""
        }
      });

      if (response.ok) {
        const data = await response.json();
        setVariations(data.clips || []);
        setIsProcessing(false);
        setProgressMessage("Matrix generation complete!");
      }
    } catch (err) {
      console.error("Error fetching results:", err);
      setError("Failed to load generated clips");
      setIsProcessing(false);
    }
  };

  // Download Premiere XML
  const downloadPremiereXML = async () => {
    if (!taskId || !session?.user?.id) return;

    try {
      const response = await fetch(`${apiUrl}/tasks/${taskId}/premiere-xml`, {
        headers: {
          "user_id": session.user.id
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `matrix_${taskId}.xml`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      console.error("Error downloading Premiere XML:", err);
      setError("Failed to download Premiere XML");
    }
  };

  // Download all clips as ZIP
  const downloadAllClips = async () => {
    if (!taskId || !session?.user?.id) return;

    try {
      const response = await fetch(`${apiUrl}/tasks/${taskId}/download-all`, {
        headers: {
          "user_id": session.user.id
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `matrix_${taskId}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      console.error("Error downloading clips:", err);
      setError("Failed to download clips");
    }
  };

  if (!session?.user) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="p-8 text-center">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 text-yellow-500" />
            <h2 className="text-xl font-semibold mb-2">Authentication Required</h2>
            <p className="text-gray-600 mb-4">Please sign in to use matrix generation</p>
            <Link href="/sign-in">
              <Button>Sign In</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
              </Link>
              <div className="flex items-center gap-3">
                <Grid3x3 className="w-6 h-6 text-black" />
                <h1 className="text-2xl font-bold text-black">Matrix Generation</h1>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {!isProcessing && variations.length === 0 ? (
          // Generation Form
          <div className="max-w-3xl mx-auto">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">Start Matrix Generation</CardTitle>
                <p className="text-sm text-gray-600">
                  Generate multiple variations of clips with AI council deliberation and customizable effects
                </p>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Source Type Selector */}
                  <div className="space-y-2">
                    <Label>Source Type</Label>
                    <Select
                      value={sourceType}
                      onValueChange={(value: "youtube" | "upload") => setSourceType(value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="upload">
                          <div className="flex items-center gap-2">
                            <Upload className="w-4 h-4" />
                            Upload Video
                          </div>
                        </SelectItem>
                        <SelectItem value="youtube">
                          <div className="flex items-center gap-2">
                            <Youtube className="w-4 h-4" />
                            YouTube URL
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Video Input */}
                  {sourceType === "youtube" ? (
                    <div className="space-y-2">
                      <Label htmlFor="youtube-url">YouTube URL</Label>
                      <Input
                        id="youtube-url"
                        type="url"
                        placeholder="https://www.youtube.com/watch?v=..."
                        value={youtubeUrl}
                        onChange={(e) => setYoutubeUrl(e.target.value)}
                      />
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Label htmlFor="video-file">Video File</Label>
                      <Input
                        id="video-file"
                        type="file"
                        accept="video/*"
                        ref={fileInputRef}
                        onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                      />
                      {uploadedFile && (
                        <p className="text-xs text-gray-600">Selected: {uploadedFile.name}</p>
                      )}
                    </div>
                  )}

                  {/* User Notes */}
                  <div className="space-y-2">
                    <Label htmlFor="user-notes">User Notes (Optional)</Label>
                    <Textarea
                      id="user-notes"
                      placeholder="Guide the AI council: e.g., 'Look for emotional moments, action sequences, and quotable lines'"
                      value={userNotes}
                      onChange={(e) => setUserNotes(e.target.value)}
                      rows={3}
                    />
                    <p className="text-xs text-gray-500">
                      These notes will guide the AI council in selecting the best clips
                    </p>
                  </div>

                  {/* Matrix Options */}
                  <div className="space-y-4 border rounded-lg p-4 bg-gray-50">
                    <h3 className="font-medium flex items-center gap-2">
                      <Film className="w-4 h-4" />
                      Matrix Options
                    </h3>

                    {/* Effect Toggles */}
                    <div className="space-y-3">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="watermark"
                          checked={matrixOptions.enable_watermark}
                          onCheckedChange={(checked) =>
                            setMatrixOptions(prev => ({ ...prev, enable_watermark: checked as boolean }))
                          }
                        />
                        <Label htmlFor="watermark" className="cursor-pointer">
                          Enable Watermark
                        </Label>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="title-card"
                          checked={matrixOptions.enable_title_card}
                          onCheckedChange={(checked) =>
                            setMatrixOptions(prev => ({ ...prev, enable_title_card: checked as boolean }))
                          }
                        />
                        <Label htmlFor="title-card" className="cursor-pointer">
                          Enable Title Card
                        </Label>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="music"
                          checked={matrixOptions.enable_music}
                          onCheckedChange={(checked) =>
                            setMatrixOptions(prev => ({ ...prev, enable_music: checked as boolean }))
                          }
                        />
                        <Label htmlFor="music" className="cursor-pointer">
                          Enable Music
                        </Label>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="captions"
                          checked={matrixOptions.enable_captions}
                          onCheckedChange={(checked) =>
                            setMatrixOptions(prev => ({ ...prev, enable_captions: checked as boolean }))
                          }
                        />
                        <Label htmlFor="captions" className="cursor-pointer">
                          Enable Captions
                        </Label>
                      </div>
                    </div>

                    {/* Title Style Selector */}
                    {matrixOptions.enable_title_card && (
                      <div className="space-y-2">
                        <Label>Title Style</Label>
                        <Select
                          value={matrixOptions.title_style}
                          onValueChange={(value: "tt3" | "adlab_standard") =>
                            setMatrixOptions(prev => ({ ...prev, title_style: value }))
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="tt3">TT3 Style</SelectItem>
                            <SelectItem value="adlab_standard">AdLab Standard</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    {/* Canvas Styles */}
                    <div className="space-y-2">
                      <Label>Canvas Styles</Label>
                      <div className="space-y-2">
                        {canvasStyleOptions.map(option => (
                          <div key={option.value} className="flex items-center space-x-2">
                            <Checkbox
                              id={option.value}
                              checked={matrixOptions.canvas_styles.includes(option.value)}
                              onCheckedChange={() => toggleCanvasStyle(option.value)}
                            />
                            <Label htmlFor={option.value} className="cursor-pointer">
                              {option.label}
                            </Label>
                          </div>
                        ))}
                      </div>
                      <p className="text-xs text-gray-500">
                        Select at least one canvas style
                      </p>
                    </div>
                  </div>

                  {/* Error Message */}
                  {error && (
                    <Alert className="border-red-200 bg-red-50">
                      <AlertCircle className="h-4 w-4 text-red-500" />
                      <AlertDescription className="text-sm text-red-700">
                        {error}
                      </AlertDescription>
                    </Alert>
                  )}

                  {/* Submit Button */}
                  <Button type="submit" className="w-full" size="lg">
                    <Film className="w-4 h-4 mr-2" />
                    Start Matrix Generation
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        ) : isProcessing || (status !== "completed" && status !== "error") ? (
          // Processing State
          <div className="max-w-3xl mx-auto space-y-6">
            <Card>
              <CardContent className="p-8">
                <div className="text-center mb-6">
                  <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-500" />
                  <h2 className="text-xl font-semibold mb-2">
                    {status === "queued" ? "Queued for Processing" : "Generating Matrix"}
                  </h2>
                  <p className="text-gray-600">{progressMessage}</p>
                </div>

                {/* Progress Bar */}
                <div className="space-y-2 mb-6">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Progress</span>
                    <span className="font-medium">{progress}%</span>
                  </div>
                  <Progress value={progress} className="h-2" />
                </div>

                {/* Status Badge */}
                <div className="flex justify-center">
                  <Badge className="bg-blue-100 text-blue-800">
                    <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                    {status}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Alert>
              <AlertDescription className="text-sm text-center">
                This process may take several minutes. This page will automatically update when complete.
              </AlertDescription>
            </Alert>
          </div>
        ) : (
          // Results View
          <div className="space-y-6">
            {/* Header Actions */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-black">Generated Variations</h2>
                <p className="text-gray-600">{variations.length} variations created</p>
              </div>
              <div className="flex gap-2">
                <Button onClick={downloadPremiereXML} variant="outline">
                  <FileText className="w-4 h-4 mr-2" />
                  Download Premiere XML
                </Button>
                <Button onClick={downloadAllClips}>
                  <Download className="w-4 h-4 mr-2" />
                  Download All Clips
                </Button>
              </div>
            </div>

            {/* Success Message */}
            <Alert className="border-green-200 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <AlertDescription className="text-sm text-green-700">
                Matrix generation complete! {variations.length} variations are ready for download.
              </AlertDescription>
            </Alert>

            {/* Video Preview */}
            {selectedVariation && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center justify-between">
                    <span>Preview: Clip {selectedVariation.clip_order}</span>
                    <Badge variant="outline">
                      {selectedVariation.temporal_variation} / {selectedVariation.canvas_variation}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <DynamicVideoPlayer
                    src={`${apiUrl}${selectedVariation.video_url}`}
                    autoPlay
                    muted
                    loop
                  />
                  <div className="mt-4 flex gap-2">
                    <Button asChild size="sm">
                      <a href={`${apiUrl}${selectedVariation.video_url}`} download={selectedVariation.filename}>
                        <Download className="w-4 h-4 mr-2" />
                        Download This Clip
                      </a>
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setSelectedVariation(null)}>
                      Close Preview
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Variations Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {variations.map((variation) => (
                <Card key={variation.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                  <CardContent className="p-4">
                    <div className="aspect-[9/16] bg-black rounded-lg mb-3 overflow-hidden relative group">
                      <video
                        src={`${apiUrl}${variation.video_url}`}
                        className="w-full h-full object-cover"
                        muted
                      />
                      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <Button
                          size="lg"
                          onClick={() => setSelectedVariation(variation)}
                          className="bg-white text-black hover:bg-gray-100"
                        >
                          <Play className="w-6 h-6" />
                        </Button>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Clip {variation.clip_order}</span>
                        <Badge variant="outline" className="text-xs">
                          {variation.variation_type}
                        </Badge>
                      </div>
                      <div className="flex gap-1 text-xs text-gray-600">
                        <Badge variant="secondary" className="text-xs">
                          {variation.temporal_variation}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {variation.canvas_variation}
                        </Badge>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        className="w-full"
                        asChild
                      >
                        <a href={`${apiUrl}${variation.video_url}`} download={variation.filename}>
                          <Download className="w-4 h-4 mr-2" />
                          Download
                        </a>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Generate Another */}
            <div className="text-center pt-8">
              <Button
                variant="outline"
                onClick={() => {
                  setVariations([]);
                  setTaskId(null);
                  setProgress(0);
                  setStatus("idle");
                  setError(null);
                  setSelectedVariation(null);
                }}
              >
                Generate Another Matrix
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
