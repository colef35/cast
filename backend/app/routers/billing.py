import os
from fastapi import APIRouter, HTTPException, Request
from app.models.subscription import CheckoutRequest, CheckoutResponse, SubscriptionStatus, PLAN_PRICES
from app.core.supabase import get_supabase

router = APIRouter(prefix="/billing", tags=["billing"])

def get_stripe():
    import stripe
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    return stripe


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(req: CheckoutRequest):
    s = get_stripe()
    price_id = os.environ.get(f"STRIPE_PRICE_{req.plan.upper()}")
    if not price_id:
        raise HTTPException(400, f"No Stripe price configured for {req.plan}")

    session = s.checkout.Session.create(
        customer_email=req.email,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=req.success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=req.cancel_url,
        metadata={"user_id": req.user_id, "plan": req.plan},
    )
    return CheckoutResponse(checkout_url=session.url)


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    secret = os.environ["STRIPE_WEBHOOK_SECRET"]

    try:
        event = get_stripe().Webhook.construct_event(payload, sig, secret)
    except Exception as e:
        raise HTTPException(400, str(e))

    db = get_supabase()

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]
        plan = session["metadata"]["plan"]
        db.table("subscriptions").insert({
            "user_id": user_id,
            "plan": plan,
            "active": True,
            "stripe_customer_id": session["customer"],
            "stripe_subscription_id": session["subscription"],
        }).execute()

    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.paused"):
        sub = event["data"]["object"]
        db.table("subscriptions").update({"active": False})\
            .eq("stripe_subscription_id", sub["id"]).execute()

    elif event["type"] == "customer.subscription.updated":
        sub = event["data"]["object"]
        plan = sub["items"]["data"][0]["price"]["metadata"].get("plan")
        if plan:
            db.table("subscriptions").update({"plan": plan, "active": sub["status"] == "active"})\
                .eq("stripe_subscription_id", sub["id"]).execute()

    return {"received": True}


@router.get("/status/{user_id}", response_model=SubscriptionStatus)
async def get_status(user_id: str):
    db = get_supabase()
    result = db.table("subscriptions").select("*").eq("user_id", user_id)\
        .eq("active", True).single().execute()
    if not result.data:
        return SubscriptionStatus(user_id=user_id, plan=None, active=False,
                                   stripe_customer_id=None, stripe_subscription_id=None)
    return SubscriptionStatus(**result.data)
