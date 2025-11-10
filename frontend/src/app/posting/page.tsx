"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useSession } from "@/lib/auth-client";
import {
  Upload,
  Copy,
  Check,
  AlertCircle,
  Loader2,
  Image as ImageIcon,
  TrendingUp,
  Hash,
  FileText,
  Sparkles
} from "lucide-react";
import Link from "next/link";

interface PlatformSuggestion {
  title: string;
  hashtags: string[];
  description: string;
  tips: string[];
}

interface AnalysisResult {
  platform: string;
  account_type: string;
  content_type: string;
  metrics: {
    views: string | null;
    likes: string | null;
    shares: string | null;
    comments: string | null;
  };
  suggestions: {
    tiktok: PlatformSuggestion;
    instagram: PlatformSuggestion;
    youtube_shorts: PlatformSuggestion;
  };
  error?: string;
}

export default function PostingHelperPage() {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const { data: session, isPending } = useSession();

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Handle drag events
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  // Handle drop
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  // Handle file input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  // Process file
  const handleFile = (file: File) => {
    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file (PNG, JPG, JPEG, etc.)');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setFile(file);
    setError(null);
    setAnalysisResult(null);

    // Create preview URL
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  // Analyze screenshot
  const analyzeScreenshot = async () => {
    if (!file) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${apiUrl}/posting/analyze-screenshot`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to analyze screenshot');
      }

      const data: AnalysisResult = await response.json();
      setAnalysisResult(data);
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err instanceof Error ? err.message : 'Failed to analyze screenshot');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Copy to clipboard
  const copyToClipboard = async (text: string, fieldName: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(fieldName);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Reset state
  const reset = () => {
    setFile(null);
    setPreviewUrl(null);
    setAnalysisResult(null);
    setError(null);
    setCopiedField(null);
  };

  if (isPending) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Please <Link href="/sign-in" className="underline">sign in</Link> to use the posting helper.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Posting Helper</h1>
        <p className="text-muted-foreground">
          Upload a screenshot to get AI-generated titles, hashtags, and descriptions for your content across platforms
        </p>
      </div>

      <div className="grid gap-8 md:grid-cols-2">
        {/* Upload Section */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Upload Screenshot</CardTitle>
              <CardDescription>
                Drag and drop or click to upload a screenshot of your content
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!file ? (
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                    dragActive
                      ? 'border-primary bg-primary/5'
                      : 'border-muted-foreground/25 hover:border-primary/50'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => document.getElementById('fileInput')?.click()}
                >
                  <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-lg font-medium mb-2">
                    {dragActive ? 'Drop your screenshot here' : 'Drag & drop your screenshot'}
                  </p>
                  <p className="text-sm text-muted-foreground mb-4">
                    or click to browse
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Supports PNG, JPG, JPEG (max 10MB)
                  </p>
                  <input
                    id="fileInput"
                    type="file"
                    accept="image/*"
                    onChange={handleChange}
                    className="hidden"
                  />
                </div>
              ) : (
                <div className="space-y-4">
                  {previewUrl && (
                    <div className="relative rounded-lg overflow-hidden border">
                      <img
                        src={previewUrl}
                        alt="Screenshot preview"
                        className="w-full h-auto"
                      />
                    </div>
                  )}
                  <div className="flex gap-2">
                    <Button
                      onClick={analyzeScreenshot}
                      disabled={isAnalyzing}
                      className="flex-1"
                    >
                      {isAnalyzing ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <Sparkles className="mr-2 h-4 w-4" />
                          Analyze Screenshot
                        </>
                      )}
                    </Button>
                    <Button
                      onClick={reset}
                      variant="outline"
                      disabled={isAnalyzing}
                    >
                      Reset
                    </Button>
                  </div>
                </div>
              )}

              {error && (
                <Alert variant="destructive" className="mt-4">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Analysis Info */}
          {analysisResult && (
            <Card className="mt-4">
              <CardHeader>
                <CardTitle>Detection Results</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Platform</span>
                  <Badge variant="secondary">{analysisResult.platform}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Account Type</span>
                  <Badge variant="outline">{analysisResult.account_type}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Content Type</span>
                  <Badge variant="outline">{analysisResult.content_type}</Badge>
                </div>

                {(analysisResult.metrics.views || analysisResult.metrics.likes) && (
                  <>
                    <Separator />
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Detected Metrics</p>
                      {analysisResult.metrics.views && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Views</span>
                          <span className="font-medium">{analysisResult.metrics.views}</span>
                        </div>
                      )}
                      {analysisResult.metrics.likes && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Likes</span>
                          <span className="font-medium">{analysisResult.metrics.likes}</span>
                        </div>
                      )}
                      {analysisResult.metrics.shares && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Shares</span>
                          <span className="font-medium">{analysisResult.metrics.shares}</span>
                        </div>
                      )}
                      {analysisResult.metrics.comments && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Comments</span>
                          <span className="font-medium">{analysisResult.metrics.comments}</span>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Results Section */}
        <div className="space-y-4">
          {analysisResult ? (
            <>
              {/* TikTok Suggestions */}
              <PlatformCard
                platform="TikTok"
                platformColor="bg-black"
                suggestion={analysisResult.suggestions.tiktok}
                copiedField={copiedField}
                onCopy={copyToClipboard}
              />

              {/* Instagram Suggestions */}
              <PlatformCard
                platform="Instagram"
                platformColor="bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500"
                suggestion={analysisResult.suggestions.instagram}
                copiedField={copiedField}
                onCopy={copyToClipboard}
              />

              {/* YouTube Shorts Suggestions */}
              <PlatformCard
                platform="YouTube Shorts"
                platformColor="bg-red-600"
                suggestion={analysisResult.suggestions.youtube_shorts}
                copiedField={copiedField}
                onCopy={copyToClipboard}
              />
            </>
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                <ImageIcon className="mx-auto h-12 w-12 mb-4 opacity-50" />
                <p>Upload a screenshot to get started</p>
                <p className="text-sm mt-2">
                  AI will analyze your screenshot and generate platform-specific content suggestions
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

// Platform Card Component
interface PlatformCardProps {
  platform: string;
  platformColor: string;
  suggestion: PlatformSuggestion;
  copiedField: string | null;
  onCopy: (text: string, fieldName: string) => void;
}

function PlatformCard({ platform, platformColor, suggestion, copiedField, onCopy }: PlatformCardProps) {
  const platformKey = platform.toLowerCase().replace(' ', '_');

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${platformColor}`} />
          <CardTitle>{platform}</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Title */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <FileText className="h-4 w-4" />
            <span>Title</span>
          </div>
          <div className="flex items-start gap-2">
            <p className="flex-1 text-sm bg-muted p-3 rounded-md">
              {suggestion.title}
            </p>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onCopy(suggestion.title, `${platformKey}_title`)}
            >
              {copiedField === `${platformKey}_title` ? (
                <Check className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Hashtags */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Hash className="h-4 w-4" />
            <span>Hashtags</span>
          </div>
          <div className="flex items-start gap-2">
            <p className="flex-1 text-sm bg-muted p-3 rounded-md">
              {suggestion.hashtags.map(tag => tag.startsWith('#') ? tag : `#${tag}`).join(' ')}
            </p>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onCopy(
                suggestion.hashtags.map(tag => tag.startsWith('#') ? tag : `#${tag}`).join(' '),
                `${platformKey}_hashtags`
              )}
            >
              {copiedField === `${platformKey}_hashtags` ? (
                <Check className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Description */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <FileText className="h-4 w-4" />
            <span>Description</span>
          </div>
          <div className="flex items-start gap-2">
            <p className="flex-1 text-sm bg-muted p-3 rounded-md">
              {suggestion.description}
            </p>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onCopy(suggestion.description, `${platformKey}_description`)}
            >
              {copiedField === `${platformKey}_description` ? (
                <Check className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Tips */}
        {suggestion.tips && suggestion.tips.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <TrendingUp className="h-4 w-4" />
              <span>Best Practices</span>
            </div>
            <ul className="space-y-1 text-sm text-muted-foreground">
              {suggestion.tips.map((tip, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-primary">•</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <Separator />

        {/* Copy All Button */}
        <Button
          variant="secondary"
          className="w-full"
          onClick={() => {
            const fullContent = `${suggestion.title}\n\n${suggestion.description}\n\n${suggestion.hashtags.map(tag => tag.startsWith('#') ? tag : `#${tag}`).join(' ')}`;
            onCopy(fullContent, `${platformKey}_all`);
          }}
        >
          {copiedField === `${platformKey}_all` ? (
            <>
              <Check className="mr-2 h-4 w-4" />
              Copied All
            </>
          ) : (
            <>
              <Copy className="mr-2 h-4 w-4" />
              Copy All
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
