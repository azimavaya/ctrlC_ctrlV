"""
middleware.py
JWT authentication and role-based access decorators.
"""
from functools import wraps
import jwt
from flask import request, jsonify, current_app
from .services.auth_service import decode_token


def token_required(f):
    """Require a valid JWT on any decorated route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Extract the Authorization header; expect "Bearer <token>"
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or malformed"}), 401

        # Strip the "Bearer " prefix to get the raw JWT string
        token = auth_header.split(" ", 1)[1]
        try:
            # Decode and verify the JWT; attach user payload to the request
            request.current_user = decode_token(token)
        except jwt.ExpiredSignatureError:
            # Token is valid but past its expiry time
            return jsonify({"error": "Token has expired, please log in again"}), 401
        except jwt.InvalidTokenError:
            # Token signature is invalid or payload is malformed
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


def role_required(*allowed_roles):
    """Require token_required first, then check the user's role claim."""
    def decorator(f):
        @token_required          # JWT must be valid before we check the role
        @wraps(f)
        def decorated(*args, **kwargs):
            # Compare the role embedded in the JWT to the allowed set
            role = request.current_user.get("role")
            if role not in allowed_roles:
                return jsonify({
                    "error": f"Access denied. Required role(s): {', '.join(allowed_roles)}"
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
