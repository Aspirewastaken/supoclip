"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Sparkles, Check, Zap, Crown, Rocket } from "lucide-react";
import Link from "next/link";

interface PricingPlan {
  id: string;
  name: string;
  price: number;
  currency: string;
  interval: string;
  features: string[];
  quota: number;
  recommended?: boolean;
  price_id?: string;
  savings?: string;
}

interface UpgradePromptProps {
  currentRole: string;
  currentUsage?: number;
  quotaLimit?: number;
  compact?: boolean;
}

export default function UpgradePrompt({
  currentRole,
  currentUsage = 0,
  quotaLimit = 10,
  compact = false
}: UpgradePromptProps) {
  const [pricingPlans, setPricingPlans] = useState<PricingPlan[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchPricing = async () => {
      try {
        const response = await fetch(`${apiUrl}/billing/pricing`);
        if (response.ok) {
          const data = await response.json();
          setPricingPlans(data.plans || []);
        }
      } catch (error) {
        console.error('Failed to fetch pricing:', error);
      }
    };

    fetchPricing();
  }, [apiUrl]);

  const handleUpgrade = async (priceId: string) => {
    setIsLoading(true);
    try {
      const sessionResponse = await fetch('/api/auth/get-session');
      const sessionData = await sessionResponse.json();
      const userId = sessionData?.user?.id;

      if (!userId) {
        throw new Error('User not authenticated');
      }

      const response = await fetch(`${apiUrl}/billing/create-checkout-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'user_id': userId
        },
        body: JSON.stringify({
          price_id: priceId,
          success_url: `${window.location.origin}/settings?upgrade=success`,
          cancel_url: `${window.location.origin}/settings?upgrade=cancelled`
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create checkout session');
      }

      const data = await response.json();

      // Redirect to Stripe checkout (or show stub message)
      if (data.url) {
        window.location.href = data.url;
      } else {
        alert(data.message || 'Checkout session created');
      }
    } catch (error) {
      console.error('Upgrade error:', error);
      alert('Failed to start upgrade process. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Don't show for admin or pro users
  if (currentRole === 'admin' || currentRole === 'pro') {
    return null;
  }

  // Compact version for inline prompts
  if (compact) {
    return (
      <Alert className="border-blue-200 bg-gradient-to-r from-blue-50 to-purple-50">
        <Sparkles className="h-4 w-4 text-blue-500" />
        <AlertDescription className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-900">
              Unlock more with SupoClip Pro
            </p>
            <p className="text-xs text-gray-600">
              Get 500 clips/month, custom branding, and priority support
            </p>
          </div>
          <Link href="/settings?tab=billing">
            <Button size="sm" className="ml-4 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600">
              <Sparkles className="w-3 h-3 mr-1" />
              Upgrade
            </Button>
          </Link>
        </AlertDescription>
      </Alert>
    );
  }

  // Full pricing card version
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-black mb-2">
          Upgrade to SupoClip Pro
        </h2>
        <p className="text-gray-600">
          Unlock powerful features and generate more viral clips
        </p>
      </div>

      {/* Current Usage Alert */}
      {currentUsage >= quotaLimit * 0.75 && (
        <Alert className="border-yellow-200 bg-yellow-50">
          <Zap className="h-4 w-4 text-yellow-500" />
          <AlertDescription className="text-sm text-yellow-700">
            You've used {currentUsage} of {quotaLimit} clips this month. Upgrade for 50x more capacity!
          </AlertDescription>
        </Alert>
      )}

      {/* Pricing Plans Grid */}
      <div className="grid md:grid-cols-2 gap-6">
        {pricingPlans
          .filter(plan => plan.id !== 'free')
          .map((plan) => (
            <Card
              key={plan.id}
              className={`relative ${
                plan.recommended
                  ? 'border-2 border-blue-500 shadow-lg'
                  : 'border-gray-200'
              }`}
            >
              {plan.recommended && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <Badge className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-3 py-1">
                    <Crown className="w-3 h-3 mr-1" />
                    Recommended
                  </Badge>
                </div>
              )}

              <CardHeader className="text-center pb-4">
                <CardTitle className="text-2xl font-bold text-black">
                  {plan.name}
                </CardTitle>
                <div className="mt-2">
                  <span className="text-4xl font-bold text-black">
                    ${plan.price}
                  </span>
                  <span className="text-gray-600">/{plan.interval}</span>
                </div>
                {plan.savings && (
                  <Badge variant="outline" className="mt-2 border-green-500 text-green-700">
                    {plan.savings}
                  </Badge>
                )}
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Features List */}
                <ul className="space-y-3">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA Button */}
                {plan.price_id && (
                  <Button
                    onClick={() => handleUpgrade(plan.price_id!)}
                    disabled={isLoading}
                    className={`w-full ${
                      plan.recommended
                        ? 'bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600'
                        : ''
                    }`}
                  >
                    {isLoading ? (
                      'Processing...'
                    ) : (
                      <>
                        <Rocket className="w-4 h-4 mr-2" />
                        Upgrade to Pro
                      </>
                    )}
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
      </div>

      {/* FAQ or Additional Info */}
      <div className="text-center text-sm text-gray-600">
        <p>
          All plans include a 14-day money-back guarantee.{" "}
          <Link href="/contact" className="text-blue-500 hover:underline">
            Contact us
          </Link>{" "}
          if you have questions.
        </p>
      </div>
    </div>
  );
}
