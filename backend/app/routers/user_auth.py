import os
import uuid
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt

from app.core.supabase import get_supabase

router = APIRouter(prefix="/user", tags=["auth"])

_SECRET = os.environ.get("JWT_SECRET", "cast-dev-secret-change-in-prod")
_ALGO = "HS256"
_bearer = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
    return f"{salt}${dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, dk_hex = stored.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


def _make_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=30),
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGO)


def _decode_token(token: str) -> dict:
    return jwt.decode(token, _SECRET, algorithms=[_ALGO])


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return _decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("/register")
def register(req: RegisterRequest):
    db = get_supabase()
    existing = db.table("users").select("id").eq("email", req.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    db.table("users").insert({
        "id": user_id,
        "email": req.email,
        "password_hash": _hash_password(req.password),
        "plan": "trial",
    }).execute()

    token = _make_token(user_id, req.email)
    return {"token": token, "user_id": user_id, "email": req.email, "plan": "trial"}


@router.post("/login")
def login(req: LoginRequest):
    db = get_supabase()
    result = db.table("users").select("*").eq("email", req.email).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = result.data[0]
    if not _verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = _make_token(user["id"], user["email"])
    return {"token": token, "user_id": user["id"], "email": user["email"], "plan": user.get("plan", "trial")}


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    result = db.table("users").select("id,email,plan,created_at").eq("id", current_user["sub"]).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    return result.data
