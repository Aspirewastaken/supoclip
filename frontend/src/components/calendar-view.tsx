"use client";

import { useState, useEffect } from "react";
import { Calendar, Clock, Trash2, Edit, CheckCircle, XCircle, AlertCircle, Loader2, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface ScheduledPost {
  id: string;
  clip_id: string;
  task_id: string;
  scheduled_time: string;
  title: string;
  status: "scheduled" | "published" | "failed" | "cancelled";
  calendar_provider: string;
  calendar_event_id: string;
  clip_metadata?: {
    filename?: string;
    duration?: number;
    relevance_score?: number;
  };
  created_at: string;
}

interface CalendarViewProps {
  showFilters?: boolean;
  limit?: number;
}

export function CalendarView({ showFilters = true, limit = 50 }: CalendarViewProps) {
  const [posts, setPosts] = useState<ScheduledPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [postToDelete, setPostToDelete] = useState<string | null>(null);

  // Load scheduled posts
  const loadPosts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter !== "all") {
        params.append("status", filter);
      }
      params.append("limit", limit.toString());

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/calendar/events?${params}`,
        {
          credentials: "include",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to load scheduled posts");
      }

      const data = await response.json();
      setPosts(data.scheduled_posts || []);
    } catch (error) {
      console.error("Failed to load posts:", error);
      toast.error("Failed to load scheduled posts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPosts();
  }, [filter]);

  // Delete a scheduled post
  const handleDelete = async (postId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/calendar/events/${postId}`,
        {
          method: "DELETE",
          credentials: "include",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to delete scheduled post");
      }

      toast.success("Scheduled post deleted");
      loadPosts();
    } catch (error) {
      console.error("Failed to delete post:", error);
      toast.error("Failed to delete scheduled post");
    }
  };

  // Cancel a scheduled post
  const handleCancel = async (postId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/calendar/events/${postId}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            status: "cancelled",
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to cancel scheduled post");
      }

      toast.success("Post cancelled");
      loadPosts();
    } catch (error) {
      console.error("Failed to cancel post:", error);
      toast.error("Failed to cancel post");
    }
  };

  // Get status badge
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "scheduled":
        return (
          <Badge variant="default" className="gap-1">
            <Clock className="h-3 w-3" />
            Scheduled
          </Badge>
        );
      case "published":
        return (
          <Badge variant="default" className="gap-1 bg-green-500 hover:bg-green-600">
            <CheckCircle className="h-3 w-3" />
            Published
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            Failed
          </Badge>
        );
      case "cancelled":
        return (
          <Badge variant="secondary" className="gap-1">
            <XCircle className="h-3 w-3" />
            Cancelled
          </Badge>
        );
      default:
        return <Badge>{status}</Badge>;
    }
  };

  // Group posts by date
  const groupedPosts = posts.reduce((acc, post) => {
    const date = new Date(post.scheduled_time).toLocaleDateString();
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(post);
    return acc;
  }, {} as Record<string, ScheduledPost[]>);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Calendar className="h-6 w-6" />
            Scheduled Posts
          </h2>
          <p className="text-muted-foreground">
            View and manage your scheduled posts
          </p>
        </div>
        <Button onClick={loadPosts} variant="outline" size="sm">
          <Loader2 className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="flex gap-2">
          <Button
            variant={filter === "all" ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter("all")}
          >
            All
          </Button>
          <Button
            variant={filter === "scheduled" ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter("scheduled")}
          >
            Scheduled
          </Button>
          <Button
            variant={filter === "published" ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter("published")}
          >
            Published
          </Button>
          <Button
            variant={filter === "cancelled" ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter("cancelled")}
          >
            Cancelled
          </Button>
          <Button
            variant={filter === "failed" ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter("failed")}
          >
            Failed
          </Button>
        </div>
      )}

      {/* Posts List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : posts.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No scheduled posts</h3>
              <p className="text-muted-foreground">
                Schedule your clips to post them at the perfect time
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedPosts).map(([date, datePosts]) => (
            <div key={date} className="space-y-3">
              <h3 className="text-lg font-semibold text-muted-foreground">{date}</h3>
              <div className="space-y-3">
                {datePosts
                  .sort(
                    (a, b) =>
                      new Date(a.scheduled_time).getTime() -
                      new Date(b.scheduled_time).getTime()
                  )
                  .map((post) => (
                    <Card key={post.id}>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="space-y-1 flex-1">
                            <CardTitle className="text-base">{post.title}</CardTitle>
                            <CardDescription className="flex items-center gap-4 text-sm">
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {new Date(post.scheduled_time).toLocaleTimeString([], {
                                  hour: "2-digit",
                                  minute: "2-digit",
                                })}
                              </span>
                              <span className="capitalize">{post.calendar_provider}</span>
                              {post.clip_metadata?.duration && (
                                <span>{post.clip_metadata.duration.toFixed(1)}s</span>
                              )}
                            </CardDescription>
                          </div>
                          {getStatusBadge(post.status)}
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                window.location.href = `/tasks/${post.task_id}#${post.clip_id}`;
                              }}
                            >
                              View Clip
                            </Button>
                          </div>
                          <div className="flex gap-2">
                            {post.status === "scheduled" && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleCancel(post.id)}
                              >
                                <XCircle className="h-4 w-4 mr-1" />
                                Cancel
                              </Button>
                            )}
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setPostToDelete(post.id);
                                setDeleteDialogOpen(true);
                              }}
                            >
                              <Trash2 className="h-4 w-4 mr-1" />
                              Delete
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Scheduled Post</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove the post from your calendar and delete the schedule. This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (postToDelete) {
                  handleDelete(postToDelete);
                  setDeleteDialogOpen(false);
                  setPostToDelete(null);
                }
              }}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
