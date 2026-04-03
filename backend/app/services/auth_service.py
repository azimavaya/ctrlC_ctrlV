"""
auth_service.py
Password hashing (bcrypt) and JWT token utilities.
"""
import datetime
import bcrypt
import jwt
from flask import current_app


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt with a random salt."""
    # bcrypt.gensalt() generates a new random salt each time
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash (constant-time comparison)."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def generate_token(user_id: int, username: str, role: str) -> str:
    """Create a signed JWT containing the user's identity and role claim."""
    payload = {
        "user_id":  user_id,
        "username": username,
        "role":     role,
        # Expiry is set from config (default 8 hours)
        "exp":      datetime.datetime.utcnow()
                    + datetime.timedelta(hours=current_app.config["JWT_EXPIRY_HOURS"]),
    }
    # Sign with HS256 (HMAC-SHA256) using the app's JWT secret
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_token(token: str) -> dict:
    """Verify and decode a JWT; raises jwt.InvalidTokenError on failure."""
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET"],
        algorithms=["HS256"],
    )
