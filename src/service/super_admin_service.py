"""
Super Admin service endpoints: threshold configuration governance.
Only SUPER_ADMIN role can access these endpoints.
"""
import csv
import json
from io import StringIO
from datetime import datetime
from urllib.parse import quote
from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..manager.threshold_manager import ThresholdManager, DEFAULT_CONFIG, SAFETY_BOUNDS
from ..utils import error, get_pagination_params, make_pagination
from ..timeutil import UTC

super_admin_bp = Blueprint("super_admin", __name__)
threshold_manager = ThresholdManager()


def _require_super_admin():
    """Check if current user has SUPER_ADMIN role."""
    claims = get_jwt() or {}
    role = claims.get("role", "USER")
    return role == "SUPER_ADMIN"


def _format_timestamp(value: datetime) -> str:
    """Format datetime as ISO string with Z suffix."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat().replace("+00:00", "Z")


@super_admin_bp.route("/thresholds/active", methods=["GET"])
@jwt_required()
def get_active_thresholds():
    """Get currently active threshold configuration.

    This endpoint is accessible to all authenticated users for dashboard display.
    """
    result = threshold_manager.get_active_config()
    return jsonify({
        "id": result["id"],
        "config": result["config"],
        "version": result["version"],
        "published_at": _format_timestamp(result["published_at"]),
        "safety_bounds": SAFETY_BOUNDS,
    }), 200


@super_admin_bp.route("/thresholds/draft", methods=["GET"])
@jwt_required()
def get_draft_threshold():
    """Get the latest draft threshold configuration."""
    if not _require_super_admin():
        return jsonify(error("403", "Forbidden: SUPER_ADMIN role required")), 403

    result = threshold_manager.get_draft_config()
    if not result:
        return jsonify({"draft": None}), 200

    return jsonify({
        "draft": {
            "id": result["id"],
            "config": result["config"],
            "version": result["version"],
            "created_at": _format_timestamp(result["created_at"]),
        }
    }), 200


@super_admin_bp.route("/thresholds/draft", methods=["POST"])
@jwt_required()
def create_draft_threshold():
    """Create a new draft threshold configuration.

    Request body:
        {
            "systolic_min": 90,
            "systolic_max": 120,
            "diastolic_min": 60,
            "diastolic_max": 90,
            "heart_rate_min": 60,
            "heart_rate_max": 90
        }
    """
    if not _require_super_admin():
        return jsonify(error("403", "Forbidden: SUPER_ADMIN role required")), 403

    user_id = get_jwt_identity()
    data = request.get_json(force=True) or {}

    # Parse config values
    try:
        config = {
            "systolic_min": int(data.get("systolic_min", 0)),
            "systolic_max": int(data.get("systolic_max", 0)),
            "diastolic_min": int(data.get("diastolic_min", 0)),
            "diastolic_max": int(data.get("diastolic_max", 0)),
            "heart_rate_min": int(data.get("heart_rate_min", 0)),
            "heart_rate_max": int(data.get("heart_rate_max", 0)),
        }
    except (TypeError, ValueError):
        return jsonify(error("400", "All threshold values must be integers")), 400

    # Validate
    is_valid, errors = threshold_manager.validate_config(config)
    if not is_valid:
        return jsonify(error("400", "Validation error", details=errors)), 400

    # Create draft
    tc = threshold_manager.create_draft(config, user_id)

    return jsonify({
        "id": tc.id,
        "config": json.loads(tc.config),
        "version": tc.version,
        "status": tc.status,
        "created_at": _format_timestamp(tc.created_at),
    }), 201


@super_admin_bp.route("/thresholds/preview", methods=["POST"])
@jwt_required()
def preview_threshold_impact():
    """Preview the impact of a threshold configuration on existing health records.

    Request body: Same as create_draft
    """
    if not _require_super_admin():
        return jsonify(error("403", "Forbidden: SUPER_ADMIN role required")), 403

    data = request.get_json(force=True) or {}

    # Parse config values
    try:
        config = {
            "systolic_min": int(data.get("systolic_min", 0)),
            "systolic_max": int(data.get("systolic_max", 0)),
            "diastolic_min": int(data.get("diastolic_min", 0)),
            "diastolic_max": int(data.get("diastolic_max", 0)),
            "heart_rate_min": int(data.get("heart_rate_min", 0)),
            "heart_rate_max": int(data.get("heart_rate_max", 0)),
        }
    except (TypeError, ValueError):
        return jsonify(error("400", "All threshold values must be integers")), 400

    # Validate
    is_valid, errors = threshold_manager.validate_config(config)
    if not is_valid:
        return jsonify(error("400", "Validation error", details=errors)), 400

    # Get preview
    impact = threshold_manager.preview_impact(config)

    return jsonify(impact), 200


@super_admin_bp.route("/thresholds/<int:config_id>/publish", methods=["POST"])
@jwt_required()
def publish_threshold(config_id: int):
    """Publish a draft threshold configuration.

    This makes the draft active and deactivates any previously active config.
    """
    if not _require_super_admin():
        return jsonify(error("403", "Forbidden: SUPER_ADMIN role required")), 403

    user_id = get_jwt_identity()

    try:
        tc = threshold_manager.publish_config(config_id, user_id)
    except ValueError as e:
        return jsonify(error("400", str(e))), 400

    return jsonify({
        "id": tc.id,
        "config": json.loads(tc.config),
        "version": tc.version,
        "status": tc.status,
        "published_at": _format_timestamp(tc.published_at),
    }), 200


@super_admin_bp.route("/thresholds/reset", methods=["POST"])
@jwt_required()
def reset_to_default():
    """Reset thresholds to default values.

    Creates a new draft with default values.
    """
    if not _require_super_admin():
        return jsonify(error("403", "Forbidden: SUPER_ADMIN role required")), 403

    user_id = get_jwt_identity()

    # Create draft with default config
    tc = threshold_manager.create_draft(DEFAULT_CONFIG.copy(), user_id)

    return jsonify({
        "id": tc.id,
        "config": json.loads(tc.config),
        "version": tc.version,
        "status": tc.status,
        "created_at": _format_timestamp(tc.created_at),
        "message": "Default threshold draft created. Publish to apply.",
    }), 201


@super_admin_bp.route("/thresholds/audit-logs", methods=["GET"])
@jwt_required()
def get_audit_logs():
    """Get paginated audit logs for threshold changes."""
    if not _require_super_admin():
        return jsonify(error("403", "Forbidden: SUPER_ADMIN role required")), 403

    page, size = get_pagination_params()
    total, logs = threshold_manager.get_audit_logs(page, size)

    # Format timestamps
    for log in logs:
        log["created_at"] = _format_timestamp(log["created_at"])

    return jsonify({
        "logs": logs,
        "pagination": make_pagination(page, size, total),
    }), 200


@super_admin_bp.route("/thresholds/audit-logs/export", methods=["GET"])
@jwt_required()
def export_audit_logs():
    """Export audit logs as CSV."""
    if not _require_super_admin():
        return jsonify(error("403", "Forbidden: SUPER_ADMIN role required")), 403

    # Get all logs (up to 10000)
    total, logs = threshold_manager.get_audit_logs(page=1, size=10000)

    # Prepare CSV
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "ID", "Config ID", "Action", "Operator ID", "Operator Username",
        "Operator Email", "Old Config", "New Config", "Created At"
    ])

    for log in logs:
        writer.writerow([
            log["id"],
            log["config_id"],
            log["action"],
            log["operator"]["id"],
            log["operator"]["username"],
            log["operator"]["email"],
            json.dumps(log["old_config"], ensure_ascii=False) if log["old_config"] else "",
            json.dumps(log["new_config"], ensure_ascii=False),
            _format_timestamp(log["created_at"]),
        ])

    # Build filename
    filename_utf8 = f"threshold_audit_logs_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"
    ascii_fallback = f"threshold_audit_logs.csv"

    # Prepend BOM for Excel UTF-8 recognition
    csv_data = '\ufeff' + buf.getvalue()

    return Response(
        csv_data,
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quote(filename_utf8)}"
        }
    )


# OPTIONS handlers for CORS preflight
@super_admin_bp.route("/thresholds/audit-logs/export", methods=["OPTIONS"])
def export_audit_logs_options():
    return "", 204


@super_admin_bp.route("/thresholds/active", methods=["OPTIONS"])
def get_active_thresholds_options():
    return "", 204
