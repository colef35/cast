from pydantic import BaseModel
from typing import Optional
from enum import Enum


class PlanTier(str, Enum):
    starter  = "starter"   # $79/mo
    growth   = "growth"    # $199/mo
    scale    = "scale"     # $499/mo
    agency   = "agency"    # $1499/mo


PLAN_PRICES = {
    PlanTier.starter: 7900,
    PlanTier.growth:  19900,
    PlanTier.scale:   49900,
    PlanTier.agency:  149900,
}

PLAN_LIMITS = {
    PlanTier.starter: {"scans_per_day": 1,  "queue_size": 10,  "products": 1},
    PlanTier.growth:  {"scans_per_day": 5,  "queue_size": 50,  "products": 3},
    PlanTier.scale:   {"scans_per_day": 20, "queue_size": 200, "products": 10},
    PlanTier.agency:  {"scans_per_day": 99, "queue_size": 999, "products": 99},
}


class CheckoutRequest(BaseModel):
    user_id: str
    email: str
    plan: PlanTier
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str


class SubscriptionStatus(BaseModel):
    user_id: str
    plan: Optional[PlanTier]
    active: bool
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
