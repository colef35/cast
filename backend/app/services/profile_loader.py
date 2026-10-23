"""
Profile loading — resolve the active ProductProfile for a run.

Order (SPEC §4.1):
  1. Database — the user's most recently updated row in `product_profiles`
     (the normal path; the API, scanners and auto-scan loop all read rows).
  2. Config fallback — for local runs, scripts and first-boot before any
     profile exists in the DB:
       CAST_PROFILE_FILE=/path/to/profile.json   a profile JSON document
       CAST_DEFAULT_PROFILE=datum+               a bundled seed profile
     The fallback profile is owned by CAST_USER_ID if set, else the zero
     UUID (config-only runs don't write per-user data back).
"""
import json
import os
from uuid import UUID

from app.models.product_profile import ProductProfile

ZERO_USER_ID = UUID(int=0)


def _fallback_user_id() -> UUID:
    raw = os.environ.get("CAST_USER_ID")
    try:
        return UUID(raw) if raw else ZERO_USER_ID
    except Exception:
        return ZERO_USER_ID


def profile_from_seed(seed: dict, user_id: UUID | None = None) -> ProductProfile:
    """Build a ProductProfile from a seed / config dict."""
    data = {k: v for k, v in seed.items() if k not in ("id", "created_at", "updated_at")}
    data["user_id"] = str(user_id or _fallback_user_id())
    return ProductProfile(**data)


def load_profile_from_config() -> ProductProfile | None:
    """Config fallback: CAST_PROFILE_FILE JSON, else CAST_DEFAULT_PROFILE seed."""
    path = os.environ.get("CAST_PROFILE_FILE")
    if path and os.path.exists(path):
        try:
            with open(path) as f:
                return profile_from_seed(json.load(f))
        except Exception:
            pass

    slug = os.environ.get("CAST_DEFAULT_PROFILE", "").strip().lower()
    if slug:
        from app.services.datum_profile import SEED_PROFILES

        seed = SEED_PROFILES.get(slug)
        if seed:
            return profile_from_seed(seed)
    return None


async def load_active_profile(user_id: UUID | None = None) -> ProductProfile | None:
    """DB first (when a user is known), config fallback second."""
    if user_id is not None:
        try:
            from app.services.product_service import ProductService

            profile = await ProductService().get_active_profile(user_id)
            if profile:
                return profile
        except Exception:
            pass
    return load_profile_from_config()
