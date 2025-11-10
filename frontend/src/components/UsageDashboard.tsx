"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Zap, TrendingUp, AlertCircle, Crown, Sparkles } from "lucide-react";
import Link from "next/link";

interface QuotaInfo {
  has_quota: boolean;
  current_usage: number;
  quota_limit: number;
  remaining: number;
  role: string;
  percentage_used: number;
}

interface UsageHistory {
  month: number;
  year: number;
  clips_generated: number;
}

interface UsageStats {
  current_month: {
    month: number;
    year: number;
    has_quota: boolean;
    current_usage: number;
    quota_limit: number;
    remaining: number;
    role: string;
  };
  history: UsageHistory[];
}

export default function UsageDashboard() {
  const [quotaInfo, setQuotaInfo] = useState<QuotaInfo | null>(null);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchUsageData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Get user session to extract user_id
        const sessionResponse = await fetch('/api/auth/get-session');
        const sessionData = await sessionResponse.json();
        const userId = sessionData?.user?.id;

        if (!userId) {
          throw new Error('User not authenticated');
        }

        // Fetch quota info
        const quotaResponse = await fetch(`${apiUrl}/quota/check`, {
          headers: {
            'user_id': userId
          }
        });

        if (!quotaResponse.ok) {
          throw new Error('Failed to fetch quota information');
        }

        const quota: QuotaInfo = await quotaResponse.json();
        setQuotaInfo(quota);

        // Fetch usage stats
        const statsResponse = await fetch(`${apiUrl}/quota/stats`, {
          headers: {
            'user_id': userId
          }
        });

        if (statsResponse.ok) {
          const stats: UsageStats = await statsResponse.json();
          setUsageStats(stats);
        }
      } catch (err) {
        console.error('Error fetching usage data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load usage data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchUsageData();
  }, [apiUrl]);

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'admin':
        return <Badge className="bg-purple-500 text-white"><Crown className="w-3 h-3 mr-1" />Admin</Badge>;
      case 'pro':
        return <Badge className="bg-gradient-to-r from-blue-500 to-purple-500 text-white"><Sparkles className="w-3 h-3 mr-1" />Pro</Badge>;
      default:
        return <Badge variant="outline">Free</Badge>;
    }
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return "bg-red-500";
    if (percentage >= 75) return "bg-yellow-500";
    return "bg-green-500";
  };

  const getMonthName = (month: number) => {
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return months[month - 1] || "";
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32 mb-2" />
          <Skeleton className="h-4 w-48" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-20 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error || !quotaInfo) {
    return (
      <Alert className="border-red-200 bg-red-50">
        <AlertCircle className="h-4 w-4 text-red-500" />
        <AlertDescription className="text-sm text-red-700">
          {error || 'Failed to load usage information'}
        </AlertDescription>
      </Alert>
    );
  }

  const isUnlimited = quotaInfo.quota_limit === -1;
  const isNearLimit = quotaInfo.percentage_used >= 75 && !isUnlimited;
  const isAtLimit = quotaInfo.remaining <= 0 && !isUnlimited;

  return (
    <div className="space-y-6">
      {/* Current Usage Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl flex items-center gap-2">
                <Zap className="w-5 h-5" />
                Usage This Month
              </CardTitle>
              <CardDescription>
                Track your clip generation quota
              </CardDescription>
            </div>
            {getRoleBadge(quotaInfo.role)}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Usage Stats */}
          <div className="flex items-end justify-between">
            <div>
              <p className="text-3xl font-bold text-black">
                {quotaInfo.current_usage}
                {!isUnlimited && <span className="text-lg text-gray-500"> / {quotaInfo.quota_limit}</span>}
              </p>
              <p className="text-sm text-gray-600">
                {isUnlimited ? 'Unlimited clips' : `${quotaInfo.remaining} clips remaining`}
              </p>
            </div>
            {!isUnlimited && (
              <div className="text-right">
                <p className="text-sm font-medium text-gray-700">{quotaInfo.percentage_used.toFixed(1)}% used</p>
              </div>
            )}
          </div>

          {/* Progress Bar */}
          {!isUnlimited && (
            <div className="space-y-2">
              <Progress
                value={Math.min(quotaInfo.percentage_used, 100)}
                className="h-3"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0</span>
                <span>{quotaInfo.quota_limit}</span>
              </div>
            </div>
          )}

          {/* Warning Messages */}
          {isAtLimit && (
            <Alert className="border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-500" />
              <AlertDescription className="text-sm text-red-700">
                You've reached your monthly quota. Upgrade to Pro for 500 clips/month!
              </AlertDescription>
            </Alert>
          )}

          {isNearLimit && !isAtLimit && (
            <Alert className="border-yellow-200 bg-yellow-50">
              <AlertCircle className="h-4 w-4 text-yellow-500" />
              <AlertDescription className="text-sm text-yellow-700">
                You're running low on clips. Consider upgrading to Pro for more capacity.
              </AlertDescription>
            </Alert>
          )}

          {/* Upgrade CTA for Free Users */}
          {quotaInfo.role === 'free' && (
            <div className="pt-4 border-t">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-black">Want more clips?</p>
                  <p className="text-sm text-gray-600">Upgrade to Pro for 500 clips/month</p>
                </div>
                <Link href="/settings?tab=billing">
                  <Button size="sm" className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600">
                    <Sparkles className="w-4 h-4 mr-1" />
                    Upgrade
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Usage History Card */}
      {usageStats && usageStats.history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Usage History
            </CardTitle>
            <CardDescription>
              Your clip generation over the last 6 months
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {usageStats.history.map((month, index) => (
                <div key={index} className="flex items-center justify-between py-2 border-b last:border-0">
                  <span className="text-sm font-medium text-gray-700">
                    {getMonthName(month.month)} {month.year}
                  </span>
                  <span className="text-sm text-gray-600">
                    {month.clips_generated} clips
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
