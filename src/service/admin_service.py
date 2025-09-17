"""
Admin service endpoints: user list, role management, password reset.
"""
from ..timeutil import UTC
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..manager.user_manager import UserManager
from ..utils import error
from ..security import validate_password_strength, generate_temp_password


admin_bp = Blueprint("admin", __name__)
user_manager = UserManager()


def _require_role(min_role: str):
    claims = get_jwt() or {}
    role = claims.get("role", "USER")
    # Order hierarchy
    order = {"USER": 0, "ADMIN": 1, "SUPER_ADMIN": 2}
    return order.get(role, 0) >= order.get(min_role, 1)


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    if not _require_role("ADMIN"):
        return jsonify(error("403", "Forbidden")), 403
    from ..models import User
    users = User.query.order_by(User.id.asc()).all()
    items = []
    for u in users:
        items.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "created_at": (u.created_at if u.created_at.tzinfo else u.created_at.replace(tzinfo=UTC)).isoformat().replace("+00:00", "Z"),
            "last_login_at": ((u.last_login_at if u.last_login_at and u.last_login_at.tzinfo else (u.last_login_at.replace(tzinfo=UTC) if u.last_login_at else None)).isoformat().replace("+00:00", "Z") if u.last_login_at else None),
            "role": u.role,
        })
    return jsonify({"items": items, "total": len(items)}), 200


@admin_bp.route("/users/<int:user_id>/promote-admin", methods=["POST"])
@jwt_required()
def promote_admin(user_id: int):
    if not _require_role("SUPER_ADMIN"):
        return jsonify(error("403", "Forbidden")), 403
    me = get_jwt_identity()
    target = user_manager.get_user(user_id)
    if not target:
        return jsonify(error("404", "User not found")), 404
    if target.role == "SUPER_ADMIN":
        return jsonify(error("400", "Cannot modify SUPER_ADMIN role")), 400
    user_manager.set_role(target, "ADMIN")
    return jsonify({"message": "Promoted to ADMIN"}), 200


@admin_bp.route("/users/<int:user_id>/demote-admin", methods=["POST"])
@jwt_required()
def demote_admin(user_id: int):
    if not _require_role("SUPER_ADMIN"):
        return jsonify(error("403", "Forbidden")), 403
    target = user_manager.get_user(user_id)
    if not target:
        return jsonify(error("404", "User not found")), 404
    if target.role == "SUPER_ADMIN":
        return jsonify(error("400", "Cannot modify SUPER_ADMIN role")), 400
    user_manager.set_role(target, "USER")
    return jsonify({"message": "Demoted to USER"}), 200


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@jwt_required()
def admin_reset_password(user_id: int):
    if not _require_role("ADMIN"):
        return jsonify(error("403", "Forbidden")), 403
    operator_id = get_jwt_identity()
    if operator_id == user_id:
        return jsonify(error("400", "Use self change-password API for your own account")), 400
    target = user_manager.get_user(user_id)
    if not target:
        return jsonify(error("404", "User not found")), 404
    # Generate a strong temporary password automatically
    temp_password = generate_temp_password(12)
    user_manager.set_password(target, temp_password, force_change_next_login=True)
    return jsonify({
        "message": "Password reset; user must change password on next login",
        "temp_password": temp_password,
    }), 200
