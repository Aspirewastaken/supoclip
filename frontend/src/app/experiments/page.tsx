"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSession } from "@/lib/auth-client";
import {
  ArrowLeft,
  TrendingUp,
  Trophy,
  Play,
  Pause,
  CheckCircle,
  AlertCircle,
  Plus,
  BarChart3,
  X,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";

// Types
interface Experiment {
  id: string;
  name: string;
  description: string;
  status: "running" | "paused" | "completed";
  winner_variation_id: string | null;
  confidence_threshold: number;
  started_at: string;
  completed_at: string | null;
  created_at: string;
}

interface Variation {
  variation_id: string;
  variation_name: string;
  metrics: {
    views: number;
    clicks: number;
    conversions: number;
    shares: number;
    likes: number;
    comments: number;
    click_through_rate: number;
    conversion_rate: number;
    engagement_rate: number;
    avg_watch_time: number;
    watch_completion_rate: number;
  };
}

interface StatisticalTest {
  metric_name: string;
  p_value: number;
  is_significant: boolean;
  confidence_level: number;
  winner_variation_id: string | null;
  winner_improvement: number;
  test_type: string;
  message: string;
}

interface ExperimentResults {
  experiment_id: string;
  experiment_name: string;
  status: string;
  variations: Variation[];
  statistical_tests: StatisticalTest[];
  overall_winner: string | null;
  overall_confidence: number;
  recommendation: string;
  should_declare_winner: boolean;
  min_sample_size_reached: boolean;
  report: string;
}

interface ClipOption {
  id: string;
  filename: string;
  task_id: string;
  duration: number;
}

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

export default function ExperimentsPage() {
  const { data: session, isPending } = useSession();
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [selectedExperiment, setSelectedExperiment] = useState<ExperimentResults | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [availableClips, setAvailableClips] = useState<ClipOption[]>([]);
  const [isLoadingResults, setIsLoadingResults] = useState(false);

  // Create experiment form state
  const [newExperiment, setNewExperiment] = useState({
    name: "",
    description: "",
    confidence_threshold: 0.95,
    variations: [
      { clip_id: "", variation_name: "" },
      { clip_id: "", variation_name: "" },
    ],
  });

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  // Fetch experiments
  useEffect(() => {
    if (session?.user?.id) {
      fetchExperiments();
      fetchAvailableClips();
    }
  }, [session]);

  const fetchExperiments = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`${backendUrl}/experiments/`, {
        headers: {
          user_id: session?.user?.id || "",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch experiments");
      }

      const data = await response.json();
      setExperiments(data.experiments || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load experiments");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAvailableClips = async () => {
    try {
      const response = await fetch(`${backendUrl}/tasks/?limit=100`, {
        headers: {
          user_id: session?.user?.id || "",
        },
      });

      if (!response.ok) return;

      const data = await response.json();
      const clips: ClipOption[] = [];

      // Extract clips from all tasks
      for (const task of data.tasks || []) {
        if (task.clips) {
          for (const clip of task.clips) {
            clips.push({
              id: clip.id,
              filename: clip.filename,
              task_id: task.id,
              duration: clip.duration,
            });
          }
        }
      }

      setAvailableClips(clips);
    } catch (err) {
      console.error("Failed to fetch clips:", err);
    }
  };

  const fetchExperimentResults = async (experimentId: string) => {
    try {
      setIsLoadingResults(true);
      setError(null);

      const response = await fetch(`${backendUrl}/experiments/${experimentId}/results`, {
        headers: {
          user_id: session?.user?.id || "",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch experiment results");
      }

      const data = await response.json();
      setSelectedExperiment(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load results");
    } finally {
      setIsLoadingResults(false);
    }
  };

  const createExperiment = async () => {
    try {
      setError(null);

      // Validation
      if (!newExperiment.name.trim()) {
        setError("Experiment name is required");
        return;
      }

      const validVariations = newExperiment.variations.filter(
        (v) => v.clip_id && v.variation_name.trim()
      );

      if (validVariations.length < 2) {
        setError("At least 2 variations are required");
        return;
      }

      const response = await fetch(`${backendUrl}/experiments/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          user_id: session?.user?.id || "",
        },
        body: JSON.stringify({
          name: newExperiment.name,
          description: newExperiment.description,
          confidence_threshold: newExperiment.confidence_threshold,
          variations: validVariations,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create experiment");
      }

      // Reset form and close dialog
      setNewExperiment({
        name: "",
        description: "",
        confidence_threshold: 0.95,
        variations: [
          { clip_id: "", variation_name: "" },
          { clip_id: "", variation_name: "" },
        ],
      });
      setShowCreateDialog(false);

      // Refresh experiments list
      await fetchExperiments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create experiment");
    }
  };

  const pauseExperiment = async (experimentId: string) => {
    try {
      const response = await fetch(`${backendUrl}/experiments/${experimentId}/pause`, {
        method: "POST",
        headers: {
          user_id: session?.user?.id || "",
        },
      });

      if (!response.ok) throw new Error("Failed to pause experiment");
      await fetchExperiments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to pause experiment");
    }
  };

  const resumeExperiment = async (experimentId: string) => {
    try {
      const response = await fetch(`${backendUrl}/experiments/${experimentId}/resume`, {
        method: "POST",
        headers: {
          user_id: session?.user?.id || "",
        },
      });

      if (!response.ok) throw new Error("Failed to resume experiment");
      await fetchExperiments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resume experiment");
    }
  };

  const declareWinner = async (experimentId: string, winnerId: string) => {
    try {
      const response = await fetch(`${backendUrl}/experiments/${experimentId}/declare-winner`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          user_id: session?.user?.id || "",
        },
        body: JSON.stringify({ winner_variation_id: winnerId }),
      });

      if (!response.ok) throw new Error("Failed to declare winner");
      await fetchExperiments();
      if (selectedExperiment?.experiment_id === experimentId) {
        await fetchExperimentResults(experimentId);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to declare winner");
    }
  };

  const addVariation = () => {
    setNewExperiment({
      ...newExperiment,
      variations: [...newExperiment.variations, { clip_id: "", variation_name: "" }],
    });
  };

  const removeVariation = (index: number) => {
    setNewExperiment({
      ...newExperiment,
      variations: newExperiment.variations.filter((_, i) => i !== index),
    });
  };

  const updateVariation = (index: number, field: string, value: string) => {
    const updated = [...newExperiment.variations];
    updated[index] = { ...updated[index], [field]: value };
    setNewExperiment({ ...newExperiment, variations: updated });
  };

  // Prepare chart data
  const getComparisonData = (variations: Variation[]) => {
    return [
      {
        metric: "CTR",
        ...variations.reduce((acc, v, i) => {
          acc[v.variation_name] = (v.metrics.click_through_rate * 100).toFixed(2);
          return acc;
        }, {} as Record<string, string>),
      },
      {
        metric: "Conversion",
        ...variations.reduce((acc, v) => {
          acc[v.variation_name] = (v.metrics.conversion_rate * 100).toFixed(2);
          return acc;
        }, {} as Record<string, string>),
      },
      {
        metric: "Engagement",
        ...variations.reduce((acc, v) => {
          acc[v.variation_name] = (v.metrics.engagement_rate * 100).toFixed(2);
          return acc;
        }, {} as Record<string, string>),
      },
      {
        metric: "Completion",
        ...variations.reduce((acc, v) => {
          acc[v.variation_name] = (v.metrics.watch_completion_rate * 100).toFixed(2);
          return acc;
        }, {} as Record<string, string>),
      },
    ];
  };

  if (isPending || isLoading) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        <div className="space-y-6">
          <Skeleton className="h-12 w-64" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (!session?.user) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Please sign in to view experiments.</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">A/B Testing Experiments</h1>
          <p className="text-muted-foreground">
            Test clip variations and find your winning formula with statistical confidence
          </p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Experiment
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New A/B Test</DialogTitle>
              <DialogDescription>
                Set up an experiment to compare different clip variations
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-6 py-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="name">Experiment Name *</Label>
                <Input
                  id="name"
                  placeholder="e.g., Font Style Comparison"
                  value={newExperiment.name}
                  onChange={(e) => setNewExperiment({ ...newExperiment, name: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="What are you testing and why?"
                  value={newExperiment.description}
                  onChange={(e) =>
                    setNewExperiment({ ...newExperiment, description: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confidence">Confidence Threshold</Label>
                <Select
                  value={newExperiment.confidence_threshold.toString()}
                  onValueChange={(value) =>
                    setNewExperiment({ ...newExperiment, confidence_threshold: parseFloat(value) })
                  }
                >
                  <SelectTrigger id="confidence">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0.90">90% (Less strict)</SelectItem>
                    <SelectItem value="0.95">95% (Recommended)</SelectItem>
                    <SelectItem value="0.99">99% (Very strict)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Minimum confidence level required to automatically declare a winner
                </p>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>Variations *</Label>
                  <Button variant="outline" size="sm" onClick={addVariation}>
                    <Plus className="h-4 w-4 mr-1" />
                    Add Variation
                  </Button>
                </div>

                {newExperiment.variations.map((variation, index) => (
                  <Card key={index}>
                    <CardContent className="pt-6">
                      <div className="flex gap-4">
                        <div className="flex-1 space-y-4">
                          <div className="space-y-2">
                            <Label>Variation Name</Label>
                            <Input
                              placeholder={`e.g., Version ${String.fromCharCode(65 + index)}`}
                              value={variation.variation_name}
                              onChange={(e) =>
                                updateVariation(index, "variation_name", e.target.value)
                              }
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>Select Clip</Label>
                            <Select
                              value={variation.clip_id}
                              onValueChange={(value) => updateVariation(index, "clip_id", value)}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Choose a clip..." />
                              </SelectTrigger>
                              <SelectContent>
                                {availableClips.map((clip) => (
                                  <SelectItem key={clip.id} value={clip.id}>
                                    {clip.filename} ({clip.duration.toFixed(1)}s)
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        {newExperiment.variations.length > 2 && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => removeVariation(index)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={createExperiment}>Create Experiment</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {error && !showCreateDialog && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Experiments List */}
      <div className="grid gap-6 mb-8">
        {experiments.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No experiments yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first A/B test to start optimizing your clips
              </p>
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create First Experiment
              </Button>
            </CardContent>
          </Card>
        ) : (
          experiments.map((experiment) => (
            <Card key={experiment.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <CardTitle>{experiment.name}</CardTitle>
                      <Badge
                        variant={
                          experiment.status === "running"
                            ? "default"
                            : experiment.status === "completed"
                            ? "secondary"
                            : "outline"
                        }
                      >
                        {experiment.status === "running" && <Play className="mr-1 h-3 w-3" />}
                        {experiment.status === "paused" && <Pause className="mr-1 h-3 w-3" />}
                        {experiment.status === "completed" && (
                          <CheckCircle className="mr-1 h-3 w-3" />
                        )}
                        {experiment.status}
                      </Badge>
                      {experiment.winner_variation_id && (
                        <Badge variant="default" className="bg-green-600">
                          <Trophy className="mr-1 h-3 w-3" />
                          Winner Declared
                        </Badge>
                      )}
                    </div>
                    {experiment.description && (
                      <CardDescription>{experiment.description}</CardDescription>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {experiment.status === "running" && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => pauseExperiment(experiment.id)}
                      >
                        <Pause className="h-4 w-4" />
                      </Button>
                    )}
                    {experiment.status === "paused" && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => resumeExperiment(experiment.id)}
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      onClick={() => fetchExperimentResults(experiment.id)}
                      disabled={isLoadingResults}
                    >
                      {isLoadingResults ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        "View Results"
                      )}
                    </Button>
                  </div>
                </div>
              </CardHeader>
            </Card>
          ))
        )}
      </div>

      {/* Results Panel */}
      {selectedExperiment && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{selectedExperiment.experiment_name}</CardTitle>
                  <CardDescription className="mt-2">
                    {selectedExperiment.recommendation}
                  </CardDescription>
                </div>
                {selectedExperiment.overall_winner && (
                  <Badge variant="default" className="bg-green-600 text-lg px-4 py-2">
                    <Trophy className="mr-2 h-5 w-5" />
                    Winner: {selectedExperiment.overall_winner.slice(0, 8)}
                    <span className="ml-2">
                      ({(selectedExperiment.overall_confidence * 100).toFixed(1)}% confidence)
                    </span>
                  </Badge>
                )}
              </div>
            </CardHeader>
          </Card>

          {/* Variations Comparison */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {selectedExperiment.variations.map((variation, index) => (
              <Card
                key={variation.variation_id}
                className={
                  variation.variation_id === selectedExperiment.overall_winner
                    ? "border-green-600 border-2"
                    : ""
                }
              >
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{variation.variation_name}</span>
                    {variation.variation_id === selectedExperiment.overall_winner && (
                      <Trophy className="h-5 w-5 text-green-600" />
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Views:</span>
                      <span className="font-semibold">{variation.metrics.views}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">CTR:</span>
                      <span className="font-semibold">
                        {(variation.metrics.click_through_rate * 100).toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Conversion:</span>
                      <span className="font-semibold">
                        {(variation.metrics.conversion_rate * 100).toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Engagement:</span>
                      <span className="font-semibold">
                        {(variation.metrics.engagement_rate * 100).toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Completion:</span>
                      <span className="font-semibold">
                        {(variation.metrics.watch_completion_rate * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Performance Comparison Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Comparison</CardTitle>
              <CardDescription>Key metrics across all variations</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={getComparisonData(selectedExperiment.variations)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="metric" />
                  <YAxis label={{ value: "Percentage", angle: -90, position: "insideLeft" }} />
                  <Tooltip />
                  <Legend />
                  {selectedExperiment.variations.map((variation, index) => (
                    <Bar
                      key={variation.variation_id}
                      dataKey={variation.variation_name}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Statistical Tests */}
          <Card>
            <CardHeader>
              <CardTitle>Statistical Significance Tests</CardTitle>
              <CardDescription>
                Results from chi-square and t-tests (p-value &lt; 0.05 = significant)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {selectedExperiment.statistical_tests.map((test, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border ${
                      test.is_significant
                        ? "border-green-600 bg-green-50 dark:bg-green-950"
                        : "border-gray-200"
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="font-semibold">{test.metric_name}</h4>
                        <p className="text-sm text-muted-foreground">{test.test_type}</p>
                      </div>
                      <Badge
                        variant={test.is_significant ? "default" : "outline"}
                        className={test.is_significant ? "bg-green-600" : ""}
                      >
                        {test.is_significant ? "SIGNIFICANT" : "Not Significant"}
                      </Badge>
                    </div>
                    <p className="text-sm mb-2">{test.message}</p>
                    {test.is_significant && test.winner_improvement > 0 && (
                      <div className="flex items-center gap-2 text-sm">
                        <TrendingUp className="h-4 w-4 text-green-600" />
                        <span className="text-green-600 font-semibold">
                          {test.winner_improvement.toFixed(1)}% improvement
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Sample Size Status */}
          <Alert
            variant={selectedExperiment.min_sample_size_reached ? "default" : "destructive"}
          >
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {selectedExperiment.min_sample_size_reached
                ? "✓ Minimum sample size reached - results are statistically valid"
                : "⚠ Need more data - continue test until minimum sample size is reached"}
            </AlertDescription>
          </Alert>
        </div>
      )}
    </div>
  );
}
