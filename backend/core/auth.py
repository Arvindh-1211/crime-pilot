"""JWT-based authentication for the Officer Dashboard."""
import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Header

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False

JWT_SECRET = os.getenv("JWT_SECRET", "crimepilot-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 12

# ---------------------------------------------------------------------------
# Officer Store (production: replace with DB)
# Passwords stored as bcrypt hashes. For dev, we pre-hash on first run.
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


def _build_officer_db() -> Dict[str, Any]:
    """Build officer DB with hashed passwords."""
    db = {}
    for username, data in _RAW_OFFICERS.items():
        entry = {k: v for k, v in data.items() if k != "password_plain"}
        if PASSLIB_AVAILABLE:
            entry["password_hash"] = pwd_context.hash(data["password_plain"])
        else:
            # Fallback: plain text (not for production)
            entry["password_hash"] = data["password_plain"]
        db[username] = entry
    return db


OFFICER_DB: Dict[str, Any] = _build_officer_db()


# ---------------------------------------------------------------------------
# Password verification
# ---------------------------------------------------------------------------

def verify_password(plain: str, hashed: str) -> bool:
    if PASSLIB_AVAILABLE:
        return pwd_context.verify(plain, hashed)
    return plain == hashed


# ---------------------------------------------------------------------------
# Token generation / verification
# ---------------------------------------------------------------------------

def create_token(username: str, officer: Dict[str, Any]) -> str:
    """Create a signed JWT token for an officer."""
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": username,
        "name": officer["name"],
        "badge": officer["badge"],
        "station": officer["station"],
        "role": officer["role"],
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token. Raises HTTPException on failure."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please log in again.")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


# ---------------------------------------------------------------------------
# FastAPI dependency — extracts + validates Bearer token from Authorization header
# ---------------------------------------------------------------------------

def get_current_officer(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """FastAPI dependency. Returns decoded token payload."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or malformed.")
    token = authorization.split(" ", 1)[1]
    return decode_token(token)


def require_admin(officer: Dict[str, Any]) -> Dict[str, Any]:
    """Require ADMIN_OFFICER role."""
    if officer.get("role") != "ADMIN_OFFICER":
        raise HTTPException(status_code=403, detail="Admin role required.")
    return officer
