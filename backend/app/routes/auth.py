"""
auth.py — Authentication and user management endpoints.

Handles login (with rate limiting and account lockout), current-user lookup,
and admin-only CRUD for user accounts and roles.
"""
import time
import re
from collections import defaultdict
from flask import Blueprint, jsonify, request
from ..db import get_db
from ..middleware import token_required, role_required
from ..services.auth_service import check_password, hash_password, generate_token

auth_bp = Blueprint("auth", __name__)

# ── Rate limiting (in-memory, per IP) ────────────────────────────────────────
_login_attempts = defaultdict(list)   # ip -> [timestamps]
MAX_LOGIN_ATTEMPTS_PER_MIN = 10
INPUT_MAX_LEN = 150


def _rate_limit_ok(ip):
    """Allow up to MAX_LOGIN_ATTEMPTS_PER_MIN login attempts per IP per minute."""
    now = time.time()
    window = [t for t in _login_attempts[ip] if now - t < 60]
    _login_attempts[ip] = window
    if len(window) >= MAX_LOGIN_ATTEMPTS_PER_MIN:
        return False
    _login_attempts[ip].append(now)
    return True


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate a user and return a JWT on success."""
    client_ip = request.remote_addr or "unknown"
    if not _rate_limit_ok(client_ip):
        return jsonify({"error": "Too many login attempts. Please wait a moment."}), 429

    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()[:INPUT_MAX_LEN]
    password = (data.get("password") or "")[:INPUT_MAX_LEN]

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if "@" in username:
        cursor.execute("""
            SELECT u.user_id, u.username, u.password_hash, u.is_active,
                   u.failed_login_attempts, u.locked_at,
                   r.role_name
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.email = %s
        """, (username,))
    else:
        cursor.execute("""
            SELECT u.user_id, u.username, u.password_hash, u.is_active,
                   u.failed_login_attempts, u.locked_at,
                   r.role_name
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.username = %s
        """, (username,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        return jsonify({"error": "Invalid username or password"}), 401

    if not user["is_active"]:
        cursor.close()
        return jsonify({"error": "Account is disabled"}), 403

    if user["locked_at"]:
        cursor.close()
        return jsonify({"error": "account_locked"}), 423

    if not check_password(password, user["password_hash"]):
        new_count = user["failed_login_attempts"] + 1
        if new_count >= 5:
            cursor.execute(
                "UPDATE users SET failed_login_attempts = %s, locked_at = NOW() WHERE user_id = %s",
                (new_count, user["user_id"])
            )
            db.commit()
            cursor.close()
            return jsonify({"error": "account_locked"}), 423
        else:
            cursor.execute(
                "UPDATE users SET failed_login_attempts = %s WHERE user_id = %s",
                (new_count, user["user_id"])
            )
            db.commit()
            cursor.close()
            return jsonify({"error": "Invalid username or password"}), 401

    cursor.execute(
        "UPDATE users SET last_login = NOW(), failed_login_attempts = 0, locked_at = NULL WHERE user_id = %s",
        (user["user_id"],)
    )
    db.commit()
    cursor.close()

    token = generate_token(user["user_id"], user["username"], user["role_name"])
    return jsonify({
        "token":    token,
        "username": user["username"],
        "role":     user["role_name"],
    })


@auth_bp.route("/me", methods=["GET"])
@token_required
def me():
    """Return the currently authenticated user's info."""
    u = request.current_user
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.user_id, u.username, u.email, u.created_at, u.last_login,
               r.role_name, r.description AS role_description
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        WHERE u.user_id = %s
    """, (u["user_id"],))
    user = cursor.fetchone()
    cursor.close()
    return jsonify(user)


# ── Admin-only: user management ──────────────────────────────────────────────

@auth_bp.route("/users", methods=["GET"])
@role_required("admin")
def list_users():
    """Return all user accounts with role info (admin only)."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.user_id, u.username, u.email, u.is_active,
               u.created_at, u.last_login, r.role_name
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        ORDER BY u.user_id
    """)
    users = cursor.fetchall()
    cursor.close()
    return jsonify(users)


@auth_bp.route("/users", methods=["POST"])
@role_required("admin")
def create_user():
    """Create a new user account (admin only)."""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role     = (data.get("role") or "user").strip()
    email    = (data.get("email") or "").strip() or None

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT role_id FROM roles WHERE role_name = %s", (role,))
    role_row = cursor.fetchone()
    if not role_row:
        cursor.close()
        return jsonify({"error": f"Unknown role '{role}'"}), 400

    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role_id) VALUES (%s, %s, %s, %s)",
            (username, email, hash_password(password), role_row["role_id"])
        )
        db.commit()
        new_id = cursor.lastrowid
    except Exception:
        cursor.close()
        return jsonify({"error": "Username or email already exists"}), 409
    cursor.close()
    return jsonify({"user_id": new_id, "username": username, "role": role}), 201


@auth_bp.route("/users/<int:user_id>", methods=["PATCH"])
@role_required("admin")
def update_user(user_id):
    """Update a user's password, role, active status, or unlock (admin only)."""
    data = request.get_json(silent=True) or {}
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if "password" in data:
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE user_id = %s",
            (hash_password(data["password"]), user_id)
        )
    if "role" in data:
        cursor.execute("SELECT role_id FROM roles WHERE role_name = %s", (data["role"],))
        r = cursor.fetchone()
        if r:
            cursor.execute("UPDATE users SET role_id = %s WHERE user_id = %s", (r["role_id"], user_id))
    if "is_active" in data:
        cursor.execute("UPDATE users SET is_active = %s WHERE user_id = %s", (data["is_active"], user_id))
    if data.get("unlock"):
        cursor.execute(
            "UPDATE users SET failed_login_attempts = 0, locked_at = NULL, is_active = TRUE WHERE user_id = %s",
            (user_id,)
        )

    db.commit()
    cursor.close()
    return jsonify({"message": "User updated"})


@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
@role_required("admin")
def delete_user(user_id):
    """Permanently delete a user account (admin only, cannot self-delete)."""
    caller = request.current_user
    if caller["user_id"] == user_id:
        return jsonify({"error": "You cannot delete your own account"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT user_id, username FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        return jsonify({"error": "User not found"}), 404

    cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    db.commit()
    cursor.close()
    return jsonify({"message": f"User '{user['username']}' deleted"})


@auth_bp.route("/roles", methods=["GET"])
@token_required
def list_roles():
    """Return all available roles (any authenticated user)."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM roles")
    roles = cursor.fetchall()
    cursor.close()
    return jsonify(roles)
