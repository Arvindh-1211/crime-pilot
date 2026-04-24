"""JWT-based authentication for the Officer Dashboard.

Uses PyJWT for token signing and bcrypt directly for password hashing
(passlib is incompatible with bcrypt 5.x on Python 3.14+).
"""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Header

JWT_SECRET    = os.getenv("JWT_SECRET", "crimepilot-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 12

# ---------------------------------------------------------------------------
# Password helpers  (bcrypt ≥ 4.x API — no passlib needed)
# ---------------------------------------------------------------------------

def _hash(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False

# ---------------------------------------------------------------------------
# Officer store  (production → replace with DB)
# ---------------------------------------------------------------------------

_RAW_OFFICERS = {
    "officer": {
        "password_plain": "officer123",
        "name": "Inspector Raj Kumar",
        "badge": "CYB-1042",
        "station": "Central Cyber Crime Coordination Centre (I4C)",
        "role": "OFFICER",
    },
    "admin": {
        "password_plain": "admin123",
        "name": "SP Arun Sharma",
        "badge": "CYB-0001",
        "station": "Central Cyber Crime Coordination Centre (I4C)",
        "role": "ADMIN_OFFICER",
    },
    "officer2": {
        "password_plain": "officer456",
        "name": "Sub-Inspector Priya Nair",
        "badge": "CYB-2031",
        "station": "Mumbai Cyber Crime Police Station",
        "role": "OFFICER",
    },
}

def _build_db() -> Dict[str, Any]:
    db = {}
    for username, data in _RAW_OFFICERS.items():
        entry = {k: v for k, v in data.items() if k != "password_plain"}
        entry["password_hash"] = _hash(data["password_plain"])
        db[username] = entry
    return db

OFFICER_DB: Dict[str, Any] = _build_db()

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_token(username: str, officer: Dict[str, Any]) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub":     username,
        "name":    officer["name"],
        "badge":   officer["badge"],
        "station": officer["station"],
        "role":    officer["role"],
        "iat":     now,
        "exp":     now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please log in again.")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_current_officer(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or malformed.")
    return decode_token(authorization.split(" ", 1)[1])

def require_admin(officer: Dict[str, Any]) -> Dict[str, Any]:
    if officer.get("role") != "ADMIN_OFFICER":
        raise HTTPException(status_code=403, detail="Admin role required.")
    return officer
