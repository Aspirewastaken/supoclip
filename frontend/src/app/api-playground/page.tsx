"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface EndpointConfig {
  method: "GET" | "POST" | "PATCH" | "DELETE" | "PUT";
  path: string;
  description: string;
  category: string;
  requiresAuth: boolean;
  bodyExample?: string;
  queryParams?: { name: string; description: string; required: boolean }[];
}

const endpoints: EndpointConfig[] = [
  // Video Processing
  {
    method: "POST",
    path: "/start",
    description: "Process video synchronously and return all clips",
    category: "Video Processing",
    requiresAuth: true,
    bodyExample: JSON.stringify({
      source: { url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ" },
      font_options: { font_family: "TikTokSans-Regular", font_size: 24, font_color: "#FFFFFF" }
    }, null, 2),
  },
  {
    method: "POST",
    path: "/start-with-progress",
    description: "Process video asynchronously with SSE progress updates",
    category: "Video Processing",
    requiresAuth: true,
    bodyExample: JSON.stringify({
      source: { url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ" },
      font_options: { font_family: "TikTokSans-Regular", font_size: 24, font_color: "#FFFFFF" }
    }, null, 2),
  },
  {
    method: "POST",
    path: "/upload",
    description: "Upload a video file",
    category: "Video Processing",
    requiresAuth: true,
  },
  // Tasks
  {
    method: "GET",
    path: "/tasks",
    description: "List all tasks for authenticated user",
    category: "Tasks",
    requiresAuth: true,
    queryParams: [{ name: "limit", description: "Maximum number of results", required: false }],
  },
  {
    method: "GET",
    path: "/tasks/{task_id}",
    description: "Get task details",
    category: "Tasks",
    requiresAuth: true,
  },
  {
    method: "GET",
    path: "/tasks/{task_id}/clips",
    description: "Get all clips for a task",
    category: "Tasks",
    requiresAuth: true,
  },
  {
    method: "PATCH",
    path: "/tasks/{task_id}",
    description: "Update task title",
    category: "Tasks",
    requiresAuth: true,
    bodyExample: JSON.stringify({ title: "Updated Title" }, null, 2),
  },
  {
    method: "DELETE",
    path: "/tasks/{task_id}",
    description: "Delete task and all clips",
    category: "Tasks",
    requiresAuth: true,
  },
  // AI Titles
  {
    method: "POST",
    path: "/ai/generate-titles",
    description: "Generate viral titles for a clip",
    category: "AI Titles",
    requiresAuth: true,
    bodyExample: JSON.stringify({
      transcript_text: "In this clip I reveal the secret to...",
      platform: "tiktok",
      num_variations: 10
    }, null, 2),
  },
  {
    method: "GET",
    path: "/ai/title-styles",
    description: "Get available title styles",
    category: "AI Titles",
    requiresAuth: false,
  },
  {
    method: "GET",
    path: "/ai/platforms",
    description: "Get supported platforms",
    category: "AI Titles",
    requiresAuth: false,
  },
  // Analytics
  {
    method: "POST",
    path: "/analytics/record",
    description: "Record analytics metrics",
    category: "Analytics",
    requiresAuth: true,
    bodyExample: JSON.stringify({
      view_metrics: {
        clip_id: "clip-123",
        platform: "tiktok",
        views: 10000,
        likes: 1500,
        comments: 200,
        shares: 300
      }
    }, null, 2),
  },
  {
    method: "GET",
    path: "/analytics/clip/{clip_id}",
    description: "Get clip performance metrics",
    category: "Analytics",
    requiresAuth: true,
  },
  {
    method: "GET",
    path: "/analytics/dashboard",
    description: "Get dashboard analytics",
    category: "Analytics",
    requiresAuth: true,
  },
  // Resources
  {
    method: "GET",
    path: "/fonts",
    description: "List available fonts",
    category: "Resources",
    requiresAuth: false,
  },
  {
    method: "GET",
    path: "/transitions",
    description: "List available transitions",
    category: "Resources",
    requiresAuth: false,
  },
];

const categories = Array.from(new Set(endpoints.map(e => e.category)));

export default function APIPlaygroundPage() {
  const [selectedEndpoint, setSelectedEndpoint] = useState<EndpointConfig | null>(null);
  const [userId, setUserId] = useState("");
  const [requestBody, setRequestBody] = useState("");
  const [pathParams, setPathParams] = useState<Record<string, string>>({});
  const [queryParams, setQueryParams] = useState<Record<string, string>>({});
  const [response, setResponse] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSelectEndpoint = (endpoint: EndpointConfig) => {
    setSelectedEndpoint(endpoint);
    setRequestBody(endpoint.bodyExample || "");
    setResponse(null);
    setError(null);
    setPathParams({});
    setQueryParams({});
  };

  const executeRequest = async () => {
    if (!selectedEndpoint) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      // Replace path parameters
      let url = selectedEndpoint.path;
      Object.entries(pathParams).forEach(([key, value]) => {
        url = url.replace(`{${key}}`, value);
      });

      // Add query parameters
      const queryString = new URLSearchParams(queryParams).toString();
      if (queryString) {
        url += `?${queryString}`;
      }

      const fullUrl = `${API_BASE_URL}${url}`;

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };

      if (selectedEndpoint.requiresAuth && userId) {
        headers["user_id"] = userId;
      }

      const options: RequestInit = {
        method: selectedEndpoint.method,
        headers,
      };

      if (requestBody && ["POST", "PATCH", "PUT"].includes(selectedEndpoint.method)) {
        options.body = requestBody;
      }

      const res = await fetch(fullUrl, options);
      const data = await res.json();

      setResponse({
        status: res.status,
        statusText: res.statusText,
        headers: Object.fromEntries(res.headers.entries()),
        body: data,
      });
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const getPathParameters = (path: string): string[] => {
    const matches = path.match(/\{([^}]+)\}/g);
    return matches ? matches.map(m => m.replace(/[{}]/g, "")) : [];
  };

  const getMethodColor = (method: string) => {
    switch (method) {
      case "GET": return "bg-blue-500";
      case "POST": return "bg-green-500";
      case "PATCH": return "bg-yellow-500";
      case "PUT": return "bg-orange-500";
      case "DELETE": return "bg-red-500";
      default: return "bg-gray-500";
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-4xl font-bold mb-2">API Playground</h1>
        <p className="text-muted-foreground">
          Test SupoClip API endpoints interactively
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sidebar - Endpoint List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Endpoints</CardTitle>
            <CardDescription>Select an endpoint to test</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue={categories[0]}>
              <TabsList className="grid w-full grid-cols-2">
                {categories.slice(0, 2).map(cat => (
                  <TabsTrigger key={cat} value={cat} className="text-xs">
                    {cat}
                  </TabsTrigger>
                ))}
              </TabsList>
              <ScrollArea className="h-[600px] mt-4">
                {categories.map(category => (
                  <TabsContent key={category} value={category} className="space-y-2">
                    {endpoints.filter(e => e.category === category).map((endpoint, idx) => (
                      <Button
                        key={idx}
                        variant={selectedEndpoint === endpoint ? "default" : "outline"}
                        className="w-full justify-start text-left"
                        onClick={() => handleSelectEndpoint(endpoint)}
                      >
                        <div className="flex items-center gap-2 w-full">
                          <Badge className={`${getMethodColor(endpoint.method)} text-white`}>
                            {endpoint.method}
                          </Badge>
                          <span className="text-sm truncate flex-1">{endpoint.path}</span>
                        </div>
                      </Button>
                    ))}
                  </TabsContent>
                ))}
              </ScrollArea>
            </Tabs>
          </CardContent>
        </Card>

        {/* Main Content - Request Configuration */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Request</CardTitle>
            <CardDescription>
              {selectedEndpoint ? selectedEndpoint.description : "Select an endpoint to get started"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {selectedEndpoint && (
              <>
                {/* Endpoint Info */}
                <div className="flex items-center gap-2">
                  <Badge className={`${getMethodColor(selectedEndpoint.method)} text-white`}>
                    {selectedEndpoint.method}
                  </Badge>
                  <code className="text-sm bg-muted px-2 py-1 rounded">
                    {API_BASE_URL}{selectedEndpoint.path}
                  </code>
                </div>

                {selectedEndpoint.requiresAuth && (
                  <div className="space-y-2">
                    <Label htmlFor="user_id">User ID (Required for Authentication)</Label>
                    <Input
                      id="user_id"
                      placeholder="Enter your user UUID"
                      value={userId}
                      onChange={(e) => setUserId(e.target.value)}
                    />
                  </div>
                )}

                {/* Path Parameters */}
                {getPathParameters(selectedEndpoint.path).length > 0 && (
                  <div className="space-y-2">
                    <Label>Path Parameters</Label>
                    {getPathParameters(selectedEndpoint.path).map(param => (
                      <div key={param} className="space-y-1">
                        <Label htmlFor={param} className="text-xs text-muted-foreground">
                          {param}
                        </Label>
                        <Input
                          id={param}
                          placeholder={`Enter ${param}`}
                          value={pathParams[param] || ""}
                          onChange={(e) => setPathParams(prev => ({ ...prev, [param]: e.target.value }))}
                        />
                      </div>
                    ))}
                  </div>
                )}

                {/* Query Parameters */}
                {selectedEndpoint.queryParams && selectedEndpoint.queryParams.length > 0 && (
                  <div className="space-y-2">
                    <Label>Query Parameters</Label>
                    {selectedEndpoint.queryParams.map(param => (
                      <div key={param.name} className="space-y-1">
                        <Label htmlFor={param.name} className="text-xs text-muted-foreground">
                          {param.name} {param.required && <span className="text-red-500">*</span>}
                        </Label>
                        <Input
                          id={param.name}
                          placeholder={param.description}
                          value={queryParams[param.name] || ""}
                          onChange={(e) => setQueryParams(prev => ({ ...prev, [param.name]: e.target.value }))}
                        />
                      </div>
                    ))}
                  </div>
                )}

                {/* Request Body */}
                {selectedEndpoint.bodyExample && (
                  <div className="space-y-2">
                    <Label htmlFor="request-body">Request Body (JSON)</Label>
                    <Textarea
                      id="request-body"
                      className="font-mono text-xs h-48"
                      value={requestBody}
                      onChange={(e) => setRequestBody(e.target.value)}
                    />
                  </div>
                )}

                <Button
                  onClick={executeRequest}
                  disabled={loading || (selectedEndpoint.requiresAuth && !userId)}
                  className="w-full"
                >
                  {loading ? "Sending Request..." : "Send Request"}
                </Button>

                <Separator />

                {/* Response */}
                <div className="space-y-2">
                  <Label>Response</Label>
                  {error && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded text-red-800">
                      <strong>Error:</strong> {error}
                    </div>
                  )}
                  {response && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant={response.status < 300 ? "default" : "destructive"}>
                          {response.status} {response.statusText}
                        </Badge>
                      </div>
                      <div className="bg-muted p-4 rounded overflow-auto max-h-96">
                        <pre className="text-xs">
                          {JSON.stringify(response.body, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}

            {!selectedEndpoint && (
              <div className="text-center py-12 text-muted-foreground">
                Select an endpoint from the sidebar to start testing
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Documentation Links */}
      <Card>
        <CardHeader>
          <CardTitle>Documentation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex gap-4">
            <a
              href={`${API_BASE_URL}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              Interactive API Docs (Swagger UI)
            </a>
            <a
              href={`${API_BASE_URL}/redoc`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              ReDoc Documentation
            </a>
            <a
              href="/docs/API.md"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              Full API Documentation
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
