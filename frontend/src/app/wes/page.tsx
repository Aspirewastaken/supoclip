"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { useSession } from "@/lib/auth-client";
import Link from "next/link";
import {
  PlayCircle,
  Film,
  Grid3x3,
  Download,
  ArrowLeft,
  Sparkles,
} from "lucide-react";

type NavigationTab = "review" | "matrix" | "export";

export default function WesPage() {
  const [activeTab, setActiveTab] = useState<NavigationTab>("review");
  const { data: session } = useSession();

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <Link href="/">
                <Button variant="ghost" size="sm" className="gap-2">
                  <ArrowLeft className="w-4 h-4" />
                  Back
                </Button>
              </Link>
              <Separator orientation="vertical" className="h-6" />
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center rounded-lg shadow-md">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-black">Wes</h1>
                  <p className="text-xs text-gray-500">
                    Workflow Enhancement System
                  </p>
                </div>
              </div>
              <Badge variant="outline" className="ml-2">
                Beta
              </Badge>
            </div>

            <div className="flex items-center gap-2">
              {session?.user && (
                <div className="text-sm text-gray-600">
                  {session.user.name || session.user.email}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="border-b bg-gray-50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1 py-2">
            <Button
              variant={activeTab === "review" ? "default" : "ghost"}
              onClick={() => setActiveTab("review")}
              className="gap-2"
            >
              <Film className="w-4 h-4" />
              Review Clips
            </Button>
            <Button
              variant={activeTab === "matrix" ? "default" : "ghost"}
              onClick={() => setActiveTab("matrix")}
              className="gap-2"
            >
              <Grid3x3 className="w-4 h-4" />
              Process Matrix
            </Button>
            <Button
              variant={activeTab === "export" ? "default" : "ghost"}
              onClick={() => setActiveTab("export")}
              className="gap-2"
            >
              <Download className="w-4 h-4" />
              Export
            </Button>
          </div>
        </div>
      </div>

      {/* Main Workspace */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Review Clips Section */}
        {activeTab === "review" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-black mb-2">
                  Review Clips
                </h2>
                <p className="text-gray-600">
                  Review and manage your generated clips from all sources
                </p>
              </div>
            </div>

            <Separator />

            {/* Placeholder for Review Clips Component */}
            <Card className="border-dashed border-2">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Film className="w-5 h-5 text-gray-400" />
                  Review Clips Content Area
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12 text-gray-500">
                  <Film className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p className="text-lg font-medium mb-2">
                    Clip review interface will be implemented here
                  </p>
                  <p className="text-sm">
                    This section will display clips with playback controls,
                    ratings, and editing options
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Process Matrix Section */}
        {activeTab === "matrix" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-black mb-2">
                  Process Matrix
                </h2>
                <p className="text-gray-600">
                  Configure and manage video processing variations and
                  parameters
                </p>
              </div>
            </div>

            <Separator />

            {/* Placeholder for Process Matrix Component */}
            <Card className="border-dashed border-2">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Grid3x3 className="w-5 h-5 text-gray-400" />
                  Process Matrix Content Area
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12 text-gray-500">
                  <Grid3x3 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p className="text-lg font-medium mb-2">
                    Processing matrix configuration will be implemented here
                  </p>
                  <p className="text-sm">
                    This section will display matrix controls, variation
                    options, and processing settings
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Export Section */}
        {activeTab === "export" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-black mb-2">Export</h2>
                <p className="text-gray-600">
                  Export your clips to various platforms and formats
                </p>
              </div>
            </div>

            <Separator />

            {/* Placeholder for Export Component */}
            <Card className="border-dashed border-2">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Download className="w-5 h-5 text-gray-400" />
                  Export Content Area
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12 text-gray-500">
                  <Download className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p className="text-lg font-medium mb-2">
                    Export options will be implemented here
                  </p>
                  <p className="text-sm">
                    This section will provide export destinations, format
                    options, and bulk operations
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
