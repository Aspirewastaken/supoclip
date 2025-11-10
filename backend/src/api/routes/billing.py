"""
Billing and Stripe Integration Routes
This is a stub implementation - integrate with actual Stripe API in production
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import os

router = APIRouter(prefix="/billing", tags=["Billing"])

# Stripe configuration (stub)
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "sk_test_...")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")

# Pricing configuration
PRICING = {
    "pro_monthly": {
        "price_id": "price_pro_monthly",
        "amount": 2900,  # $29.00 in cents
        "currency": "usd",
        "interval": "month"
    },
    "pro_yearly": {
        "price_id": "price_pro_yearly",
        "amount": 29000,  # $290.00 in cents (2 months free)
        "currency": "usd",
        "interval": "year"
    }
}


class CreateCheckoutSessionRequest(BaseModel):
    """Request model for creating Stripe checkout session"""
    price_id: str
    success_url: str
    cancel_url: str


class CreatePortalSessionRequest(BaseModel):
    """Request model for creating Stripe customer portal session"""
    return_url: str


class SubscriptionResponse(BaseModel):
    """Response model for subscription information"""
    user_id: str
    role: str
    subscription_status: str
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    subscription_current_period_end: Optional[str]


@router.get(
    "/pricing",
    summary="Get Pricing Plans",
    description="Get all available pricing plans and their details"
)
async def get_pricing():
    """
    Get pricing information for all plans

    Returns:
        Dictionary of pricing plans with details
    """
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "10 clips per month",
                    "AI-powered clip selection",
                    "Basic subtitles",
                    "Standard fonts",
                    "Email support"
                ],
                "quota": 10
            },
            {
                "id": "pro_monthly",
                "name": "Pro (Monthly)",
                "price": 29,
                "currency": "usd",
                "interval": "month",
                "price_id": PRICING["pro_monthly"]["price_id"],
                "features": [
                    "500 clips per month",
                    "AI-powered clip selection",
                    "Advanced subtitles",
                    "Custom fonts & branding",
                    "Transition effects",
                    "Priority email support",
                    "API access"
                ],
                "quota": 500,
                "recommended": True
            },
            {
                "id": "pro_yearly",
                "name": "Pro (Yearly)",
                "price": 290,
                "currency": "usd",
                "interval": "year",
                "price_id": PRICING["pro_yearly"]["price_id"],
                "features": [
                    "500 clips per month",
                    "AI-powered clip selection",
                    "Advanced subtitles",
                    "Custom fonts & branding",
                    "Transition effects",
                    "Priority email support",
                    "API access",
                    "Save $58/year (2 months free)"
                ],
                "quota": 500,
                "savings": "2 months free"
            }
        ]
    }


@router.post(
    "/create-checkout-session",
    summary="Create Stripe Checkout Session",
    description="Create a Stripe checkout session for upgrading to Pro (STUB)"
)
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    user_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Stripe checkout session (stub implementation)

    In production, this would:
    1. Create a Stripe customer if not exists
    2. Create a checkout session with the price_id
    3. Return the session URL for redirect

    Args:
        request: Checkout session configuration

    Returns:
        Checkout session URL
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="user_id header required")

    try:
        # Get user info
        user_query = await db.execute(
            text("SELECT email, stripe_customer_id FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        user_row = user_query.fetchone()

        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")

        email, stripe_customer_id = user_row

        # STUB: In production, integrate with Stripe API
        # import stripe
        # stripe.api_key = STRIPE_API_KEY
        #
        # if not stripe_customer_id:
        #     customer = stripe.Customer.create(email=email, metadata={"user_id": user_id})
        #     stripe_customer_id = customer.id
        #     await db.execute(
        #         text("UPDATE users SET stripe_customer_id = :customer_id WHERE id = :user_id"),
        #         {"customer_id": stripe_customer_id, "user_id": user_id}
        #     )
        #     await db.commit()
        #
        # session = stripe.checkout.Session.create(
        #     customer=stripe_customer_id,
        #     payment_method_types=["card"],
        #     line_items=[{"price": request.price_id, "quantity": 1}],
        #     mode="subscription",
        #     success_url=request.success_url,
        #     cancel_url=request.cancel_url,
        #     metadata={"user_id": user_id}
        # )
        #
        # return {"url": session.url, "session_id": session.id}

        # STUB response
        return {
            "url": f"{request.success_url}?session_id=cs_test_stub",
            "session_id": "cs_test_stub",
            "message": "STUB: Stripe integration not configured. In production, this would redirect to Stripe checkout.",
            "note": "Set STRIPE_API_KEY environment variable to enable Stripe integration"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


@router.post(
    "/create-portal-session",
    summary="Create Stripe Customer Portal Session",
    description="Create a Stripe customer portal session for managing subscription (STUB)"
)
async def create_portal_session(
    request: CreatePortalSessionRequest,
    user_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Stripe customer portal session (stub implementation)

    In production, this would:
    1. Create a portal session for the customer
    2. Return the portal URL for redirect

    Args:
        request: Portal session configuration

    Returns:
        Portal session URL
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="user_id header required")

    try:
        # Get user's Stripe customer ID
        customer_query = await db.execute(
            text("SELECT stripe_customer_id FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        stripe_customer_id = customer_query.scalar()

        if not stripe_customer_id:
            raise HTTPException(status_code=400, detail="No active subscription found")

        # STUB: In production, integrate with Stripe API
        # import stripe
        # stripe.api_key = STRIPE_API_KEY
        #
        # session = stripe.billing_portal.Session.create(
        #     customer=stripe_customer_id,
        #     return_url=request.return_url
        # )
        #
        # return {"url": session.url}

        # STUB response
        return {
            "url": f"{request.return_url}?portal=stub",
            "message": "STUB: Stripe integration not configured. In production, this would redirect to Stripe customer portal.",
            "note": "Set STRIPE_API_KEY environment variable to enable Stripe integration"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create portal session: {str(e)}")


@router.get(
    "/subscription",
    response_model=SubscriptionResponse,
    summary="Get Subscription Status",
    description="Get current user's subscription status and details"
)
async def get_subscription_status(
    user_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get subscription information for the current user

    Returns:
        Subscription status and details
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="user_id header required")

    try:
        # Get user subscription info
        query = await db.execute(
            text("""
                SELECT role, subscription_status, stripe_customer_id,
                       stripe_subscription_id, subscription_current_period_end
                FROM users
                WHERE id = :user_id
            """),
            {"user_id": user_id}
        )
        result = query.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        return SubscriptionResponse(
            user_id=user_id,
            role=result[0],
            subscription_status=result[1],
            stripe_customer_id=result[2],
            stripe_subscription_id=result[3],
            subscription_current_period_end=result[4].isoformat() if result[4] else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get subscription: {str(e)}")


@router.post(
    "/webhook",
    summary="Stripe Webhook Handler",
    description="Handle Stripe webhook events (STUB)"
)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events (stub implementation)

    In production, this would:
    1. Verify webhook signature
    2. Handle events like:
       - checkout.session.completed -> upgrade user to pro
       - customer.subscription.updated -> update subscription status
       - customer.subscription.deleted -> downgrade user to free
       - invoice.payment_failed -> mark subscription as past_due

    Returns:
        Success status
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        # STUB: In production, verify webhook signature
        # import stripe
        # stripe.api_key = STRIPE_API_KEY
        #
        # event = stripe.Webhook.construct_event(
        #     payload, sig_header, STRIPE_WEBHOOK_SECRET
        # )
        #
        # if event["type"] == "checkout.session.completed":
        #     session = event["data"]["object"]
        #     user_id = session["metadata"]["user_id"]
        #     customer_id = session["customer"]
        #     subscription_id = session["subscription"]
        #
        #     # Upgrade user to pro
        #     await db.execute(
        #         text("""
        #             UPDATE users
        #             SET role = 'pro',
        #                 stripe_customer_id = :customer_id,
        #                 stripe_subscription_id = :subscription_id,
        #                 subscription_status = 'active',
        #                 subscription_current_period_end = :period_end
        #             WHERE id = :user_id
        #         """),
        #         {
        #             "customer_id": customer_id,
        #             "subscription_id": subscription_id,
        #             "period_end": datetime.fromtimestamp(session["current_period_end"]),
        #             "user_id": user_id
        #         }
        #     )
        #     await db.commit()
        #
        # elif event["type"] == "customer.subscription.deleted":
        #     subscription = event["data"]["object"]
        #     # Downgrade user to free
        #     await db.execute(
        #         text("""
        #             UPDATE users
        #             SET role = 'free', subscription_status = 'canceled'
        #             WHERE stripe_subscription_id = :subscription_id
        #         """),
        #         {"subscription_id": subscription["id"]}
        #     )
        #     await db.commit()

        return {
            "status": "success",
            "message": "STUB: Webhook received but not processed. Configure Stripe integration to handle webhooks."
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")


@router.post(
    "/cancel-subscription",
    summary="Cancel Subscription",
    description="Cancel the current user's subscription (STUB)"
)
async def cancel_subscription(
    user_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel user's subscription (stub implementation)

    In production, this would cancel the Stripe subscription
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="user_id header required")

    try:
        # Get subscription ID
        query = await db.execute(
            text("SELECT stripe_subscription_id FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        subscription_id = query.scalar()

        if not subscription_id:
            raise HTTPException(status_code=400, detail="No active subscription found")

        # STUB: In production, cancel via Stripe API
        # import stripe
        # stripe.api_key = STRIPE_API_KEY
        # stripe.Subscription.delete(subscription_id)

        # Update database
        await db.execute(
            text("""
                UPDATE users
                SET subscription_status = 'canceled'
                WHERE id = :user_id
            """),
            {"user_id": user_id}
        )
        await db.commit()

        return {
            "success": True,
            "message": "Subscription canceled (STUB). In production, this would cancel the Stripe subscription.",
            "note": "User will be downgraded to free tier at the end of the billing period"
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to cancel subscription: {str(e)}")


# Import get_db at the end to avoid circular imports
from ...database import get_db
