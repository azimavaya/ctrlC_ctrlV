# JWT authentication and role-based access decorators.

from functools import wraps
import jwt
from flask import request, jsonify, current_app
from .services.auth_service import decode_token


def token_required(f):
    """Require a valid JWT on any decorated route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Expect "Authorization: Bearer <token>"
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or malformed"}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            # Decode and verify the JWT, attach user to request
            request.current_user = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired, please log in again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


def role_required(*allowed_roles):
    """Require token_required first, then check the user's role claim."""
    def decorator(f):
        # JWT must be valid before we check the role
        @token_required
        @wraps(f)
        def decorated(*args, **kwargs):
            role = request.current_user.get("role")
            if role not in allowed_roles:
                return jsonify({
                    "error": f"Access denied. Required role(s): {', '.join(allowed_roles)}"
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
