"use client";

import { useState } from "react";
import { Calendar, Clock, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

interface CalendarSchedulerProps {
  clipId: string;
  clipTitle?: string;
  onScheduled?: () => void;
}

interface CalendarProvider {
  id: string;
  provider: string;
  is_active: boolean;
  calendar_name?: string;
}

export function CalendarScheduler({ clipId, clipTitle, onScheduled }: CalendarSchedulerProps) {
  const [loading, setLoading] = useState(false);
  const [providers, setProviders] = useState<CalendarProvider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [scheduledDate, setScheduledDate] = useState("");
  const [scheduledTime, setScheduledTime] = useState("");
  const [loadingProviders, setLoadingProviders] = useState(false);

  // Load calendar providers
  const loadProviders = async () => {
    setLoadingProviders(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/calendar/credentials`, {
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error("Failed to load calendar providers");
      }

      const data = await response.json();
      setProviders(data.credentials || []);

      // Auto-select first active provider
      const activeProvider = data.credentials.find((p: CalendarProvider) => p.is_active);
      if (activeProvider) {
        setSelectedProvider(activeProvider.id);
      }
    } catch (error) {
      console.error("Failed to load providers:", error);
      toast.error("Failed to load calendar providers");
    } finally {
      setLoadingProviders(false);
    }
  };

  // Schedule the post
  const handleSchedule = async () => {
    if (!selectedProvider) {
      toast.error("Please select a calendar provider");
      return;
    }

    if (!scheduledDate || !scheduledTime) {
      toast.error("Please select a date and time");
      return;
    }

    setLoading(true);
    try {
      // Combine date and time into ISO format
      const scheduledDateTime = new Date(`${scheduledDate}T${scheduledTime}:00`).toISOString();

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/calendar/schedule`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          clip_id: clipId,
          scheduled_time: scheduledDateTime,
          provider: providers.find((p) => p.id === selectedProvider)?.provider,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to schedule post");
      }

      const data = await response.json();

      toast.success("Post scheduled successfully!", {
        description: `Your clip will be posted on ${new Date(scheduledDateTime).toLocaleString()}`,
      });

      // Reset form
      setScheduledDate("");
      setScheduledTime("");

      // Call callback
      onScheduled?.();
    } catch (error) {
      console.error("Failed to schedule post:", error);
      toast.error(error instanceof Error ? error.message : "Failed to schedule post");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Schedule Post
        </CardTitle>
        <CardDescription>
          Schedule this clip to be posted at a specific time
          {clipTitle && ` - ${clipTitle}`}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Calendar Provider Selection */}
        <div className="space-y-2">
          <Label htmlFor="provider">Calendar Provider</Label>
          {!providers.length ? (
            <Button
              variant="outline"
              onClick={loadProviders}
              disabled={loadingProviders}
              className="w-full"
            >
              {loadingProviders ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading providers...
                </>
              ) : (
                <>
                  <Calendar className="mr-2 h-4 w-4" />
                  Load Calendar Providers
                </>
              )}
            </Button>
          ) : (
            <Select value={selectedProvider} onValueChange={setSelectedProvider}>
              <SelectTrigger id="provider">
                <SelectValue placeholder="Select a calendar" />
              </SelectTrigger>
              <SelectContent>
                {providers.map((provider) => (
                  <SelectItem key={provider.id} value={provider.id}>
                    <div className="flex items-center gap-2">
                      <span className="capitalize">{provider.provider}</span>
                      {provider.calendar_name && (
                        <span className="text-muted-foreground">
                          - {provider.calendar_name}
                        </span>
                      )}
                      {provider.is_active && (
                        <CheckCircle className="h-3 w-3 text-green-500" />
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        {/* Date Selection */}
        <div className="space-y-2">
          <Label htmlFor="date">Date</Label>
          <Input
            id="date"
            type="date"
            value={scheduledDate}
            onChange={(e) => setScheduledDate(e.target.value)}
            min={new Date().toISOString().split("T")[0]}
          />
        </div>

        {/* Time Selection */}
        <div className="space-y-2">
          <Label htmlFor="time">Time</Label>
          <Input
            id="time"
            type="time"
            value={scheduledTime}
            onChange={(e) => setScheduledTime(e.target.value)}
          />
        </div>

        {/* Preview */}
        {scheduledDate && scheduledTime && (
          <div className="rounded-lg bg-muted p-3 text-sm">
            <div className="flex items-start gap-2">
              <Clock className="h-4 w-4 mt-0.5 text-muted-foreground" />
              <div>
                <p className="font-medium">Scheduled for:</p>
                <p className="text-muted-foreground">
                  {new Date(`${scheduledDate}T${scheduledTime}:00`).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Schedule Button */}
        <Button
          onClick={handleSchedule}
          disabled={loading || !selectedProvider || !scheduledDate || !scheduledTime}
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Scheduling...
            </>
          ) : (
            <>
              <Calendar className="mr-2 h-4 w-4" />
              Schedule Post
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
