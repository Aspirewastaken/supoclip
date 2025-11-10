"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useSession } from "@/lib/auth-client";
import {
  Users,
  Activity,
  Video,
  HardDrive,
  AlertCircle,
  CheckCircle,
  Loader2,
  Settings,
  Clock,
  XCircle,
  RefreshCw,
  Database,
  Server,
  FileText,
  BarChart3,
  Shield,
  Search,
  Filter,
  Download
} from "lucide-react";
import Link from "next/link";

interface SystemStats {
  total_users: number;
  total_tasks: number;
  total_clips: number;
  tasks_processing: number;
  tasks_queued: number;
  tasks_completed_today: number;
  tasks_failed_today: number;
}

interface UserData {
  id: string;
  name: string;
  email: string;
  emailVerified: boolean;
  createdAt: string;
  task_count: number;
  clip_count: number;
  last_activity: string;
}

interface TaskData {
  id: string;
  user_id: string;
  user_email: string;
  source_title: string;
  status: string;
  progress: number;
  progress_message: string;
  created_at: string;
  updated_at: string;
  clips_count: number;
}

interface StorageMetrics {
  total_clips: number;
  total_size_mb: number;
  clips_directory: string;
  uploads_directory: string;
  average_clip_size_mb: number;
}

interface ErrorLog {
  timestamp: string;
  level: string;
  message: string;
  user_id?: string;
  task_id?: string;
}

interface WorkerHealth {
  status: string;
  active_workers: number;
  queue_size: number;
  last_heartbeat: string;
}

export default function AdminDashboard() {
  const { data: session, isPending } = useSession();
  const [activeTab, setActiveTab] = useState<"overview" | "users" | "tasks" | "storage" | "workers" | "errors" | "config">("overview");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [users, setUsers] = useState<UserData[]>([]);
  const [tasks, setTasks] = useState<TaskData[]>([]);
  const [storageMetrics, setStorageMetrics] = useState<StorageMetrics | null>(null);
  const [workerHealth, setWorkerHealth] = useState<WorkerHealth | null>(null);
  const [errorLogs, setErrorLogs] = useState<ErrorLog[]>([]);

  // Filter states
  const [userSearch, setUserSearch] = useState("");
  const [taskStatusFilter, setTaskStatusFilter] = useState<string>("all");

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Admin check - for now, check if user email contains "admin" or specific admin IDs
  const isAdmin = session?.user?.email?.includes("admin") || session?.user?.email?.includes("support");

  useEffect(() => {
    if (!session?.user?.id || !isAdmin) return;

    loadDashboardData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, [session?.user?.id, isAdmin, apiUrl]);

  const loadDashboardData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      await Promise.all([
        loadSystemStats(),
        loadUsers(),
        loadRecentTasks(),
        loadStorageMetrics(),
        loadWorkerHealth(),
      ]);
    } catch (err) {
      console.error("Error loading dashboard data:", err);
      setError(err instanceof Error ? err.message : "Failed to load dashboard data");
    } finally {
      setIsLoading(false);
    }
  };

  const loadSystemStats = async () => {
    try {
      const response = await fetch(`${apiUrl}/admin/stats`, {
        headers: {
          'user_id': session?.user?.id || '',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSystemStats(data);
      } else {
        // Fallback: construct stats from available endpoints
        const tasksResponse = await fetch(`${apiUrl}/tasks/`, {
          headers: { 'user_id': session?.user?.id || '' },
        });

        if (tasksResponse.ok) {
          const tasksData = await tasksResponse.json();
          const tasks = tasksData.tasks || [];

          // Calculate stats from tasks
          const processing = tasks.filter((t: TaskData) => t.status === "processing").length;
          const queued = tasks.filter((t: TaskData) => t.status === "queued").length;
          const today = new Date().toDateString();
          const completedToday = tasks.filter((t: TaskData) =>
            t.status === "completed" && new Date(t.updated_at).toDateString() === today
          ).length;
          const failedToday = tasks.filter((t: TaskData) =>
            t.status === "failed" && new Date(t.updated_at).toDateString() === today
          ).length;

          setSystemStats({
            total_users: 0, // Would need separate endpoint
            total_tasks: tasks.length,
            total_clips: tasks.reduce((sum: number, t: TaskData) => sum + (t.clips_count || 0), 0),
            tasks_processing: processing,
            tasks_queued: queued,
            tasks_completed_today: completedToday,
            tasks_failed_today: failedToday,
          });
        }
      }
    } catch (err) {
      console.error("Error loading system stats:", err);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await fetch(`${apiUrl}/admin/users`, {
        headers: {
          'user_id': session?.user?.id || '',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUsers(data.users || []);
      }
    } catch (err) {
      console.error("Error loading users:", err);
    }
  };

  const loadRecentTasks = async () => {
    try {
      const response = await fetch(`${apiUrl}/admin/tasks`, {
        headers: {
          'user_id': session?.user?.id || '',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTasks(data.tasks || []);
      }
    } catch (err) {
      console.error("Error loading tasks:", err);
    }
  };

  const loadStorageMetrics = async () => {
    try {
      const response = await fetch(`${apiUrl}/admin/storage`, {
        headers: {
          'user_id': session?.user?.id || '',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStorageMetrics(data);
      }
    } catch (err) {
      console.error("Error loading storage metrics:", err);
    }
  };

  const loadWorkerHealth = async () => {
    try {
      const response = await fetch(`${apiUrl}/health/db`);

      if (response.ok) {
        const data = await response.json();
        setWorkerHealth({
          status: data.status || "unknown",
          active_workers: 1,
          queue_size: systemStats?.tasks_queued || 0,
          last_heartbeat: new Date().toISOString(),
        });
      }
    } catch (err) {
      console.error("Error loading worker health:", err);
    }
  };

  const handleCancelTask = async (taskId: string) => {
    if (!confirm("Are you sure you want to cancel this task?")) return;

    try {
      const response = await fetch(`${apiUrl}/admin/tasks/${taskId}/cancel`, {
        method: 'POST',
        headers: {
          'user_id': session?.user?.id || '',
        },
      });

      if (response.ok) {
        alert("Task cancelled successfully");
        loadRecentTasks();
      } else {
        alert("Failed to cancel task");
      }
    } catch (err) {
      console.error("Error cancelling task:", err);
      alert("Error cancelling task");
    }
  };

  const handleRetryTask = async (taskId: string) => {
    if (!confirm("Are you sure you want to retry this task?")) return;

    try {
      const response = await fetch(`${apiUrl}/admin/tasks/${taskId}/retry`, {
        method: 'POST',
        headers: {
          'user_id': session?.user?.id || '',
        },
      });

      if (response.ok) {
        alert("Task queued for retry");
        loadRecentTasks();
      } else {
        alert("Failed to retry task");
      }
    } catch (err) {
      console.error("Error retrying task:", err);
      alert("Error retrying task");
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
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
          <Shield className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h1 className="text-3xl font-bold text-black mb-4">Sign In Required</h1>
          <p className="text-gray-600 mb-8">
            You need to be signed in to access the admin dashboard.
          </p>
          <Link href="/sign-in">
            <Button size="lg">Sign In</Button>
          </Link>
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-white">
        <div className="max-w-4xl mx-auto px-4 py-24 text-center">
          <Shield className="w-16 h-16 mx-auto mb-4 text-red-500" />
          <h1 className="text-3xl font-bold text-black mb-4">Access Denied</h1>
          <p className="text-gray-600 mb-8">
            You do not have permission to access the admin dashboard.
          </p>
          <Link href="/">
            <Button size="lg">Return to Home</Button>
          </Link>
        </div>
      </div>
    );
  }

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(userSearch.toLowerCase()) ||
    user.email.toLowerCase().includes(userSearch.toLowerCase())
  );

  const filteredTasks = tasks.filter(task =>
    taskStatusFilter === "all" || task.status === taskStatusFilter
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-black">Admin Dashboard</h1>
                <p className="text-sm text-gray-600">System management and monitoring</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={loadDashboardData}
                disabled={isLoading}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Link href="/">
                <Button variant="outline" size="sm">
                  Back to App
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1 overflow-x-auto">
            {[
              { id: "overview", label: "Overview", icon: BarChart3 },
              { id: "users", label: "Users", icon: Users },
              { id: "tasks", label: "Tasks", icon: Activity },
              { id: "storage", label: "Storage", icon: HardDrive },
              { id: "workers", label: "Workers", icon: Server },
              { id: "errors", label: "Error Logs", icon: AlertCircle },
              { id: "config", label: "Configuration", icon: Settings },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors whitespace-nowrap ${
                    activeTab === tab.id
                      ? "border-blue-600 text-blue-600 font-medium"
                      : "border-transparent text-gray-600 hover:text-gray-900"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {error && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-500" />
            <AlertDescription className="text-sm text-red-700">
              {error}
            </AlertDescription>
          </Alert>
        )}

        {/* Overview Tab */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* System Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Total Users</p>
                      <p className="text-3xl font-bold text-black">
                        {isLoading ? <Skeleton className="h-8 w-16" /> : systemStats?.total_users || 0}
                      </p>
                    </div>
                    <Users className="w-8 h-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Total Tasks</p>
                      <p className="text-3xl font-bold text-black">
                        {isLoading ? <Skeleton className="h-8 w-16" /> : systemStats?.total_tasks || 0}
                      </p>
                    </div>
                    <Activity className="w-8 h-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Total Clips</p>
                      <p className="text-3xl font-bold text-black">
                        {isLoading ? <Skeleton className="h-8 w-16" /> : systemStats?.total_clips || 0}
                      </p>
                    </div>
                    <Video className="w-8 h-8 text-purple-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Processing</p>
                      <p className="text-3xl font-bold text-black">
                        {isLoading ? <Skeleton className="h-8 w-16" /> : systemStats?.tasks_processing || 0}
                      </p>
                    </div>
                    <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Processing Queue Status */}
            <Card>
              <CardHeader>
                <CardTitle>Processing Queue Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Queued</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {systemStats?.tasks_queued || 0}
                    </p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Completed Today</p>
                    <p className="text-2xl font-bold text-green-600">
                      {systemStats?.tasks_completed_today || 0}
                    </p>
                  </div>
                  <div className="text-center p-4 bg-orange-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Processing</p>
                    <p className="text-2xl font-bold text-orange-600">
                      {systemStats?.tasks_processing || 0}
                    </p>
                  </div>
                  <div className="text-center p-4 bg-red-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Failed Today</p>
                    <p className="text-2xl font-bold text-red-600">
                      {systemStats?.tasks_failed_today || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Button variant="outline" className="h-auto py-4 flex-col gap-2">
                    <Users className="w-6 h-6" />
                    <span className="text-sm">Manage Users</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 flex-col gap-2">
                    <Activity className="w-6 h-6" />
                    <span className="text-sm">View Tasks</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 flex-col gap-2">
                    <Database className="w-6 h-6" />
                    <span className="text-sm">Database Backup</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 flex-col gap-2">
                    <FileText className="w-6 h-6" />
                    <span className="text-sm">Export Logs</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === "users" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>User Management</CardTitle>
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                      <Input
                        placeholder="Search users..."
                        value={userSearch}
                        onChange={(e) => setUserSearch(e.target.value)}
                        className="pl-9 w-64"
                      />
                    </div>
                    <Button size="sm">
                      <Download className="w-4 h-4 mr-2" />
                      Export
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="p-4 border rounded-lg">
                        <Skeleton className="h-4 w-48 mb-2" />
                        <Skeleton className="h-3 w-32" />
                      </div>
                    ))}
                  </div>
                ) : filteredUsers.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <Users className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                    <p>No users found</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {filteredUsers.map((user) => (
                      <div key={user.id} className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <p className="font-semibold text-black">{user.name}</p>
                              {user.emailVerified && (
                                <Badge className="bg-green-100 text-green-800 text-xs">
                                  <CheckCircle className="w-3 h-3 mr-1" />
                                  Verified
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-gray-600">{user.email}</p>
                            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                              <span>Tasks: {user.task_count || 0}</span>
                              <span>Clips: {user.clip_count || 0}</span>
                              <span>Joined: {formatDate(user.createdAt)}</span>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm">View</Button>
                            <Button variant="outline" size="sm">Edit</Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tasks Tab */}
        {activeTab === "tasks" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Task Monitoring</CardTitle>
                  <div className="flex items-center gap-2">
                    <select
                      value={taskStatusFilter}
                      onChange={(e) => setTaskStatusFilter(e.target.value)}
                      className="px-3 py-2 border rounded-lg text-sm"
                    >
                      <option value="all">All Status</option>
                      <option value="queued">Queued</option>
                      <option value="processing">Processing</option>
                      <option value="completed">Completed</option>
                      <option value="failed">Failed</option>
                    </select>
                    <Button size="sm">
                      <Download className="w-4 h-4 mr-2" />
                      Export
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="p-4 border rounded-lg">
                        <Skeleton className="h-4 w-64 mb-2" />
                        <Skeleton className="h-3 w-48" />
                      </div>
                    ))}
                  </div>
                ) : filteredTasks.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <Activity className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                    <p>No tasks found</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {filteredTasks.map((task) => (
                      <div key={task.id} className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <p className="font-semibold text-black">{task.source_title}</p>
                              {task.status === "completed" && (
                                <Badge className="bg-green-100 text-green-800">
                                  <CheckCircle className="w-3 h-3 mr-1" />
                                  Completed
                                </Badge>
                              )}
                              {task.status === "processing" && (
                                <Badge className="bg-blue-100 text-blue-800">
                                  <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                                  Processing
                                </Badge>
                              )}
                              {task.status === "queued" && (
                                <Badge className="bg-yellow-100 text-yellow-800">
                                  <Clock className="w-3 h-3 mr-1" />
                                  Queued
                                </Badge>
                              )}
                              {task.status === "failed" && (
                                <Badge className="bg-red-100 text-red-800">
                                  <XCircle className="w-3 h-3 mr-1" />
                                  Failed
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-gray-600">{task.user_email}</p>
                            {task.progress_message && (
                              <p className="text-xs text-gray-500 mt-1">{task.progress_message}</p>
                            )}
                            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                              <span>Progress: {task.progress}%</span>
                              <span>Clips: {task.clips_count || 0}</span>
                              <span>Created: {formatDate(task.created_at)}</span>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Link href={`/tasks/${task.id}`}>
                              <Button variant="outline" size="sm">View</Button>
                            </Link>
                            {task.status === "processing" && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleCancelTask(task.id)}
                              >
                                <XCircle className="w-4 h-4" />
                              </Button>
                            )}
                            {task.status === "failed" && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleRetryTask(task.id)}
                              >
                                <RefreshCw className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Storage Tab */}
        {activeTab === "storage" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Storage Usage Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3 mb-2">
                      <HardDrive className="w-5 h-5 text-blue-500" />
                      <p className="text-sm text-gray-600">Total Storage</p>
                    </div>
                    <p className="text-2xl font-bold text-black">
                      {storageMetrics ? formatBytes(storageMetrics.total_size_mb * 1024 * 1024) : "N/A"}
                    </p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3 mb-2">
                      <Video className="w-5 h-5 text-purple-500" />
                      <p className="text-sm text-gray-600">Total Clips</p>
                    </div>
                    <p className="text-2xl font-bold text-black">
                      {storageMetrics?.total_clips || 0}
                    </p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3 mb-2">
                      <BarChart3 className="w-5 h-5 text-green-500" />
                      <p className="text-sm text-gray-600">Avg Clip Size</p>
                    </div>
                    <p className="text-2xl font-bold text-black">
                      {storageMetrics ? formatBytes(storageMetrics.average_clip_size_mb * 1024 * 1024) : "N/A"}
                    </p>
                  </div>
                </div>

                <Separator className="my-6" />

                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <HardDrive className="w-5 h-5 text-gray-500" />
                      <div>
                        <p className="text-sm font-medium text-black">Clips Directory</p>
                        <p className="text-xs text-gray-600">{storageMetrics?.clips_directory || "/tmp/clips"}</p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm">Browse</Button>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <HardDrive className="w-5 h-5 text-gray-500" />
                      <div>
                        <p className="text-sm font-medium text-black">Uploads Directory</p>
                        <p className="text-xs text-gray-600">{storageMetrics?.uploads_directory || "/tmp/uploads"}</p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm">Browse</Button>
                  </div>
                </div>

                <Separator className="my-6" />

                <div className="flex gap-2">
                  <Button variant="outline">
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Recalculate Storage
                  </Button>
                  <Button variant="outline">
                    <Download className="w-4 h-4 mr-2" />
                    Export Report
                  </Button>
                  <Button variant="destructive">
                    Clean Old Files
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Workers Tab */}
        {activeTab === "workers" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Worker Health Monitoring</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      {workerHealth?.status === "healthy" ? (
                        <CheckCircle className="w-6 h-6 text-green-500" />
                      ) : (
                        <AlertCircle className="w-6 h-6 text-red-500" />
                      )}
                      <div>
                        <p className="font-semibold text-black">System Status</p>
                        <p className="text-sm text-gray-600">
                          {workerHealth?.status === "healthy" ? "All systems operational" : "System issues detected"}
                        </p>
                      </div>
                    </div>
                    <Badge className={workerHealth?.status === "healthy" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                      {workerHealth?.status || "Unknown"}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-gray-600 mb-1">Active Workers</p>
                      <p className="text-2xl font-bold text-black">{workerHealth?.active_workers || 0}</p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-gray-600 mb-1">Queue Size</p>
                      <p className="text-2xl font-bold text-black">{workerHealth?.queue_size || 0}</p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-gray-600 mb-1">Last Heartbeat</p>
                      <p className="text-sm font-medium text-black">
                        {workerHealth?.last_heartbeat ? formatDate(workerHealth.last_heartbeat) : "N/A"}
                      </p>
                    </div>
                  </div>

                  <Alert>
                    <Server className="h-4 w-4" />
                    <AlertDescription>
                      Worker health monitoring is currently tracking database connectivity.
                      For full worker monitoring, backend endpoints need to be implemented.
                    </AlertDescription>
                  </Alert>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Error Logs Tab */}
        {activeTab === "errors" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Error Log Viewer</CardTitle>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Filter className="w-4 h-4 mr-2" />
                      Filter
                    </Button>
                    <Button variant="outline" size="sm">
                      <Download className="w-4 h-4 mr-2" />
                      Export Logs
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {errorLogs.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-400" />
                    <p>No recent errors logged</p>
                    <p className="text-sm mt-2">System is running smoothly</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {errorLogs.map((log, index) => (
                      <div key={index} className="p-3 border rounded-lg bg-red-50">
                        <div className="flex items-start gap-3">
                          <AlertCircle className="w-4 h-4 text-red-500 mt-0.5" />
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge className="bg-red-100 text-red-800">{log.level}</Badge>
                              <span className="text-xs text-gray-500">{formatDate(log.timestamp)}</span>
                            </div>
                            <p className="text-sm text-black">{log.message}</p>
                            {log.task_id && (
                              <p className="text-xs text-gray-600 mt-1">Task: {log.task_id}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <Alert className="mt-4">
                  <FileText className="h-4 w-4" />
                  <AlertDescription>
                    Error logging requires backend implementation. Backend logs are available in <code>logs/backend.log</code>
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Configuration Tab */}
        {activeTab === "config" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>System Configuration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 border rounded-lg">
                    <p className="font-semibold text-black mb-2">AI Configuration</p>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Model Provider:</span>
                        <span className="text-black">OpenAI / Anthropic / Google</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Transcript Service:</span>
                        <span className="text-black">AssemblyAI</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Default Clip Duration:</span>
                        <span className="text-black">10-45 seconds</span>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 border rounded-lg">
                    <p className="font-semibold text-black mb-2">Storage Configuration</p>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Temp Directory:</span>
                        <span className="text-black">/tmp</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Max Upload Size:</span>
                        <span className="text-black">500 MB</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Auto-cleanup:</span>
                        <span className="text-black">7 days</span>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 border rounded-lg">
                    <p className="font-semibold text-black mb-2">API Configuration</p>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">API URL:</span>
                        <span className="text-black">{apiUrl}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">CORS:</span>
                        <span className="text-black">Enabled (*)</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Rate Limiting:</span>
                        <span className="text-black">100 req/min</span>
                      </div>
                    </div>
                  </div>

                  <Alert>
                    <Settings className="h-4 w-4" />
                    <AlertDescription>
                      Configuration management UI requires backend implementation.
                      Current settings are read from environment variables.
                    </AlertDescription>
                  </Alert>

                  <div className="flex gap-2">
                    <Button variant="outline">
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Reload Configuration
                    </Button>
                    <Button variant="outline">
                      <Download className="w-4 h-4 mr-2" />
                      Export Config
                    </Button>
                    <Button>
                      Save Changes
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
