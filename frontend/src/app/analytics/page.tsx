"use client";

import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useSession } from "@/lib/auth-client";
import {
  ArrowLeft,
  TrendingUp,
  Eye,
  Heart,
  Clock,
  Download,
  AlertCircle,
  BarChart3,
  ArrowUpDown,
  Calendar,
} from "lucide-react";
import Link from "next/link";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { format, subDays, startOfDay, endOfDay } from "date-fns";

// Types
interface DashboardStats {
  total_clips: number;
  total_clips_with_metrics: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  total_engagements: number;
  avg_engagement_rate: number;
  avg_watch_time: number;
  avg_retention_rate: number;
  top_performing_clips: TopPerformingClip[];
  platform_breakdown: Record<string, PlatformStats>;
}

interface TopPerformingClip {
  clip_id: string;
  filename: string;
  duration: number;
  relevance_score: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  engagement_rate: number;
  retention_rate: number;
  video_url: string;
}

interface PlatformStats {
  clips_count: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  total_engagements: number;
}

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];

const PLATFORM_NAMES: Record<string, string> = {
  tiktok: "TikTok",
  youtube_shorts: "YouTube Shorts",
  instagram_reels: "Instagram Reels",
  facebook: "Facebook",
  twitter: "Twitter",
  linkedin: "LinkedIn",
};

export default function AnalyticsPage() {
  const { data: session, isPending } = useSession();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortColumn, setSortColumn] = useState<keyof TopPerformingClip>("total_views");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [filterPlatform, setFilterPlatform] = useState<string>("all");
  const [dateRange, setDateRange] = useState<{ start: Date; end: Date }>({
    start: subDays(new Date(), 30),
    end: new Date(),
  });

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    const fetchStats = async () => {
      if (!session?.user?.id) return;

      try {
        setIsLoading(true);
        const response = await fetch(`${apiUrl}/analytics/dashboard?user_id=${session.user.id}&limit=100`, {
          headers: {
            user_id: session.user.id,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch analytics: ${response.status}`);
        }

        const data = await response.json();
        setStats(data);
      } catch (err) {
        console.error("Error fetching analytics:", err);
        setError(err instanceof Error ? err.message : "Failed to load analytics");
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, [session?.user?.id, apiUrl]);

  // Calculate performance over time data (mock data for demonstration)
  const performanceOverTime = useMemo(() => {
    if (!stats) return [];

    const days = 30;
    const data = [];
    for (let i = days - 1; i >= 0; i--) {
      const date = subDays(new Date(), i);
      const baseViews = stats.total_views / days;
      const variance = (Math.random() - 0.5) * baseViews * 0.4;

      data.push({
        date: format(date, "MMM dd"),
        views: Math.round(baseViews + variance),
        engagement: Math.round((stats.avg_engagement_rate + (Math.random() - 0.5) * 5) * 10) / 10,
      });
    }
    return data;
  }, [stats]);

  // Platform comparison data
  const platformComparisonData = useMemo(() => {
    if (!stats) return [];

    return Object.entries(stats.platform_breakdown).map(([platform, data]) => ({
      platform: PLATFORM_NAMES[platform] || platform,
      views: data.total_views,
      engagements: data.total_engagements,
      clips: data.clips_count,
    }));
  }, [stats]);

  // Clips by platform (pie chart)
  const clipsByPlatform = useMemo(() => {
    if (!stats) return [];

    return Object.entries(stats.platform_breakdown).map(([platform, data]) => ({
      name: PLATFORM_NAMES[platform] || platform,
      value: data.clips_count,
    }));
  }, [stats]);

  // Filter and sort clips
  const filteredAndSortedClips = useMemo(() => {
    if (!stats) return [];

    let filtered = stats.top_performing_clips;

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter((clip) =>
        clip.filename.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Sort
    filtered = [...filtered].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];
      const multiplier = sortDirection === "asc" ? 1 : -1;
      return (aVal > bVal ? 1 : -1) * multiplier;
    });

    return filtered;
  }, [stats, searchQuery, sortColumn, sortDirection]);

  const handleSort = (column: keyof TopPerformingClip) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortDirection("desc");
    }
  };

  const exportToCSV = () => {
    if (!stats) return;

    const headers = [
      "Clip ID",
      "Filename",
      "Duration",
      "Views",
      "Likes",
      "Comments",
      "Shares",
      "Engagement Rate",
      "Retention Rate",
      "Relevance Score",
    ];

    const rows = filteredAndSortedClips.map((clip) => [
      clip.clip_id,
      clip.filename,
      clip.duration.toFixed(2),
      clip.total_views,
      clip.total_likes,
      clip.total_comments,
      clip.total_shares,
      clip.engagement_rate.toFixed(2),
      clip.retention_rate.toFixed(2),
      clip.relevance_score.toFixed(2),
    ]);

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((row) => row.join(","))].join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `supoclip-analytics-${format(new Date(), "yyyy-MM-dd")}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + "M";
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + "K";
    }
    return num.toString();
  };

  if (isPending) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center p-4">
        <div className="space-y-4">
          <Skeleton className="h-4 w-32 mx-auto" />
          <Skeleton className="h-4 w-48 mx-auto" />
          <Skeleton className="h-4 w-24 mx-auto" />
        </div>
      </div>
    );
  }

  if (!session?.user) {
    return (
      <div className="min-h-screen bg-white">
        <div className="max-w-4xl mx-auto px-4 py-24 text-center">
          <h1 className="text-3xl font-bold text-black mb-4">Sign In Required</h1>
          <p className="text-gray-600 mb-8">You need to be signed in to view analytics.</p>
          <Link href="/sign-in">
            <Button size="lg">Sign In</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center gap-4 mb-4">
            <Link href="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="w-4 h-4" />
                Back
              </Button>
            </Link>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-black mb-2">Analytics Dashboard</h1>
              <p className="text-gray-600">Track your clip performance across all platforms</p>
            </div>
            <Button onClick={exportToCSV} disabled={!stats || filteredAndSortedClips.length === 0}>
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {isLoading ? (
          <div className="grid gap-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <Card key={i}>
                  <CardContent className="p-6">
                    <Skeleton className="h-4 w-24 mb-2" />
                    <Skeleton className="h-8 w-32" />
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ) : error ? (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : !stats ? (
          <Card>
            <CardContent className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-8 h-8 text-gray-400" />
              </div>
              <h2 className="text-xl font-semibold text-black mb-2">No Analytics Data</h2>
              <p className="text-gray-600 mb-6">Start generating clips to see your analytics.</p>
              <Link href="/">
                <Button>Create First Clip</Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Overview Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-gray-600">Total Views</p>
                    <Eye className="w-5 h-5 text-blue-500" />
                  </div>
                  <p className="text-3xl font-bold text-black">{formatNumber(stats.total_views)}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Across {stats.total_clips} clips
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-gray-600">Avg Engagement</p>
                    <Heart className="w-5 h-5 text-red-500" />
                  </div>
                  <p className="text-3xl font-bold text-black">
                    {stats.avg_engagement_rate.toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatNumber(stats.total_engagements)} total engagements
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-gray-600">Best Performing</p>
                    <TrendingUp className="w-5 h-5 text-green-500" />
                  </div>
                  <p className="text-2xl font-bold text-black truncate">
                    {stats.top_performing_clips[0]?.filename.substring(0, 15) || "N/A"}...
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatNumber(stats.top_performing_clips[0]?.total_views || 0)} views
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-gray-600">Total Watch Time</p>
                    <Clock className="w-5 h-5 text-purple-500" />
                  </div>
                  <p className="text-3xl font-bold text-black">
                    {stats.avg_watch_time.toFixed(1)}s
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {stats.avg_retention_rate.toFixed(1)}% retention
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Charts Row 1 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Performance Over Time */}
              <Card>
                <CardHeader>
                  <CardTitle>Performance Over Time</CardTitle>
                  <CardDescription>Views and engagement rate trends (Last 30 days)</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={performanceOverTime}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12 }}
                        angle={-45}
                        textAnchor="end"
                        height={60}
                      />
                      <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
                      <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Legend />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="views"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        name="Views"
                      />
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="engagement"
                        stroke="#10b981"
                        strokeWidth={2}
                        name="Engagement %"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Clips by Platform */}
              <Card>
                <CardHeader>
                  <CardTitle>Clips by Platform</CardTitle>
                  <CardDescription>Distribution of clips across platforms</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={clipsByPlatform}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {clipsByPlatform.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Platform Comparison Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Platform Comparison</CardTitle>
                <CardDescription>Views and engagements by platform</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={platformComparisonData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="platform" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="views" fill="#3b82f6" name="Views" />
                    <Bar dataKey="engagements" fill="#10b981" name="Engagements" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Clip Performance Table */}
            <Card>
              <CardHeader>
                <CardTitle>Clip Performance</CardTitle>
                <CardDescription>Detailed performance metrics for all clips</CardDescription>
              </CardHeader>
              <CardContent>
                {/* Filters */}
                <div className="flex flex-col md:flex-row gap-4 mb-6">
                  <div className="flex-1">
                    <Input
                      placeholder="Search clips..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full"
                    />
                  </div>
                  <Select value={filterPlatform} onValueChange={setFilterPlatform}>
                    <SelectTrigger className="w-full md:w-48">
                      <SelectValue placeholder="All Platforms" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Platforms</SelectItem>
                      {Object.keys(stats.platform_breakdown).map((platform) => (
                        <SelectItem key={platform} value={platform}>
                          {PLATFORM_NAMES[platform] || platform}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="border-b">
                      <tr className="text-left">
                        <th className="pb-3 font-semibold text-sm text-gray-600">
                          <button
                            onClick={() => handleSort("filename")}
                            className="flex items-center gap-1 hover:text-black"
                          >
                            Clip Name
                            <ArrowUpDown className="w-3 h-3" />
                          </button>
                        </th>
                        <th className="pb-3 font-semibold text-sm text-gray-600">
                          <button
                            onClick={() => handleSort("total_views")}
                            className="flex items-center gap-1 hover:text-black"
                          >
                            Views
                            <ArrowUpDown className="w-3 h-3" />
                          </button>
                        </th>
                        <th className="pb-3 font-semibold text-sm text-gray-600">
                          <button
                            onClick={() => handleSort("total_likes")}
                            className="flex items-center gap-1 hover:text-black"
                          >
                            Likes
                            <ArrowUpDown className="w-3 h-3" />
                          </button>
                        </th>
                        <th className="pb-3 font-semibold text-sm text-gray-600">
                          <button
                            onClick={() => handleSort("total_comments")}
                            className="flex items-center gap-1 hover:text-black"
                          >
                            Comments
                            <ArrowUpDown className="w-3 h-3" />
                          </button>
                        </th>
                        <th className="pb-3 font-semibold text-sm text-gray-600">
                          <button
                            onClick={() => handleSort("engagement_rate")}
                            className="flex items-center gap-1 hover:text-black"
                          >
                            Engagement
                            <ArrowUpDown className="w-3 h-3" />
                          </button>
                        </th>
                        <th className="pb-3 font-semibold text-sm text-gray-600">
                          <button
                            onClick={() => handleSort("retention_rate")}
                            className="flex items-center gap-1 hover:text-black"
                          >
                            Retention
                            <ArrowUpDown className="w-3 h-3" />
                          </button>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredAndSortedClips.map((clip) => (
                        <tr key={clip.clip_id} className="border-b hover:bg-gray-50">
                          <td className="py-4">
                            <div className="font-medium text-black truncate max-w-xs">
                              {clip.filename}
                            </div>
                            <div className="text-xs text-gray-500">
                              {clip.duration.toFixed(1)}s • Score: {clip.relevance_score.toFixed(2)}
                            </div>
                          </td>
                          <td className="py-4 font-semibold">{formatNumber(clip.total_views)}</td>
                          <td className="py-4">{formatNumber(clip.total_likes)}</td>
                          <td className="py-4">{formatNumber(clip.total_comments)}</td>
                          <td className="py-4">
                            <Badge
                              className={
                                clip.engagement_rate > 10
                                  ? "bg-green-100 text-green-800"
                                  : clip.engagement_rate > 5
                                  ? "bg-yellow-100 text-yellow-800"
                                  : "bg-gray-100 text-gray-800"
                              }
                            >
                              {clip.engagement_rate.toFixed(1)}%
                            </Badge>
                          </td>
                          <td className="py-4">
                            <Badge
                              className={
                                clip.retention_rate > 70
                                  ? "bg-green-100 text-green-800"
                                  : clip.retention_rate > 50
                                  ? "bg-yellow-100 text-yellow-800"
                                  : "bg-gray-100 text-gray-800"
                              }
                            >
                              {clip.retention_rate.toFixed(1)}%
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {filteredAndSortedClips.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No clips match your search criteria
                  </div>
                )}

                <div className="mt-4 text-sm text-gray-500">
                  Showing {filteredAndSortedClips.length} of {stats.top_performing_clips.length} clips
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
