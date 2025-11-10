"use client";

import { useState } from "react";
import { Calendar, Plus, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CalendarView } from "@/components/calendar-view";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

export default function CalendarPage() {
  const [activeTab, setActiveTab] = useState<"view" | "settings">("view");
  const [addingProvider, setAddingProvider] = useState(false);
  const [providerType, setProviderType] = useState<"google" | "icloud" | "caldav">("google");

  // CalDAV form state
  const [caldavUrl, setCaldavUrl] = useState("");
  const [caldavUsername, setCaldavUsername] = useState("");
  const [caldavPassword, setCaldavPassword] = useState("");
  const [caldavCalendarName, setCaldavCalendarName] = useState("");

  // Handle Google OAuth
  const handleGoogleConnect = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/calendar/oauth/google/url`,
        {
          credentials: "include",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to get OAuth URL");
      }

      const data = await response.json();
      window.location.href = data.auth_url;
    } catch (error) {
      console.error("Failed to connect Google Calendar:", error);
      toast.error("Failed to connect Google Calendar");
    }
  };

  // Handle CalDAV/iCloud setup
  const handleCalDAVConnect = async () => {
    if (!caldavUsername || !caldavPassword) {
      toast.error("Please enter username and password");
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/calendar/credentials/caldav`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            provider: providerType,
            url: providerType === "icloud" ? undefined : caldavUrl,
            username: caldavUsername,
            password: caldavPassword,
            calendar_name: caldavCalendarName || undefined,
          }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to connect calendar");
      }

      toast.success("Calendar connected successfully");

      // Reset form
      setCaldavUrl("");
      setCaldavUsername("");
      setCaldavPassword("");
      setCaldavCalendarName("");
      setAddingProvider(false);
    } catch (error) {
      console.error("Failed to connect calendar:", error);
      toast.error(error instanceof Error ? error.message : "Failed to connect calendar");
    }
  };

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Calendar className="h-8 w-8" />
          Calendar Integration
        </h1>
        <p className="text-muted-foreground mt-2">
          Schedule your clips to be posted at the perfect time
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <Button
          variant={activeTab === "view" ? "default" : "ghost"}
          onClick={() => setActiveTab("view")}
        >
          <Calendar className="h-4 w-4 mr-2" />
          Scheduled Posts
        </Button>
        <Button
          variant={activeTab === "settings" ? "default" : "ghost"}
          onClick={() => setActiveTab("settings")}
        >
          <Settings className="h-4 w-4 mr-2" />
          Calendar Settings
        </Button>
      </div>

      {/* Content */}
      {activeTab === "view" ? (
        <CalendarView />
      ) : (
        <div className="space-y-6">
          {/* Connected Calendars */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Connected Calendars</CardTitle>
                  <CardDescription>
                    Manage your calendar integrations
                  </CardDescription>
                </div>
                <Button
                  onClick={() => setAddingProvider(!addingProvider)}
                  variant={addingProvider ? "outline" : "default"}
                >
                  {addingProvider ? "Cancel" : (
                    <>
                      <Plus className="h-4 w-4 mr-2" />
                      Add Calendar
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {addingProvider && (
                <div className="space-y-4 p-4 border rounded-lg bg-muted/50">
                  <div className="space-y-2">
                    <Label>Calendar Provider</Label>
                    <Select
                      value={providerType}
                      onValueChange={(value: "google" | "icloud" | "caldav") =>
                        setProviderType(value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="google">Google Calendar</SelectItem>
                        <SelectItem value="icloud">iCloud Calendar</SelectItem>
                        <SelectItem value="caldav">CalDAV (Generic)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {providerType === "google" ? (
                    <div className="space-y-4">
                      <p className="text-sm text-muted-foreground">
                        Connect your Google Calendar using OAuth. You'll be redirected to
                        Google to authorize access.
                      </p>
                      <Button onClick={handleGoogleConnect} className="w-full">
                        Connect Google Calendar
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {providerType === "caldav" && (
                        <div className="space-y-2">
                          <Label htmlFor="caldav-url">CalDAV URL</Label>
                          <Input
                            id="caldav-url"
                            type="url"
                            placeholder="https://caldav.example.com"
                            value={caldavUrl}
                            onChange={(e) => setCaldavUrl(e.target.value)}
                          />
                        </div>
                      )}

                      <div className="space-y-2">
                        <Label htmlFor="username">
                          {providerType === "icloud" ? "Apple ID" : "Username"}
                        </Label>
                        <Input
                          id="username"
                          type="text"
                          placeholder={
                            providerType === "icloud"
                              ? "your-email@icloud.com"
                              : "username"
                          }
                          value={caldavUsername}
                          onChange={(e) => setCaldavUsername(e.target.value)}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="password">
                          {providerType === "icloud"
                            ? "App-Specific Password"
                            : "Password"}
                        </Label>
                        <Input
                          id="password"
                          type="password"
                          placeholder="••••••••"
                          value={caldavPassword}
                          onChange={(e) => setCaldavPassword(e.target.value)}
                        />
                        {providerType === "icloud" && (
                          <p className="text-xs text-muted-foreground">
                            Generate an app-specific password at{" "}
                            <a
                              href="https://appleid.apple.com"
                              target="_blank"
                              rel="noopener noreferrer"
                              className="underline"
                            >
                              appleid.apple.com
                            </a>
                          </p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="calendar-name">
                          Calendar Name (Optional)
                        </Label>
                        <Input
                          id="calendar-name"
                          type="text"
                          placeholder="Calendar"
                          value={caldavCalendarName}
                          onChange={(e) => setCaldavCalendarName(e.target.value)}
                        />
                      </div>

                      <Button onClick={handleCalDAVConnect} className="w-full">
                        Connect {providerType === "icloud" ? "iCloud" : "CalDAV"} Calendar
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Instructions */}
          <Card>
            <CardHeader>
              <CardTitle>Setup Instructions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">Google Calendar</h4>
                <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground">
                  <li>Click "Connect Google Calendar"</li>
                  <li>Sign in to your Google account</li>
                  <li>Grant calendar access permissions</li>
                  <li>You'll be redirected back to schedule posts</li>
                </ol>
              </div>

              <Separator />

              <div>
                <h4 className="font-semibold mb-2">iCloud Calendar</h4>
                <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground">
                  <li>Go to appleid.apple.com and sign in</li>
                  <li>Navigate to Security &gt; App-Specific Passwords</li>
                  <li>Generate a new password for SupoClip</li>
                  <li>Enter your Apple ID and app-specific password above</li>
                </ol>
              </div>

              <Separator />

              <div>
                <h4 className="font-semibold mb-2">Generic CalDAV</h4>
                <p className="text-sm text-muted-foreground">
                  Enter your CalDAV server URL, username, and password. This works with
                  Nextcloud, OwnCloud, and other CalDAV-compatible services.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
