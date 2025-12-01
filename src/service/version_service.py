"""
Version endpoint.
"""
from flask import Blueprint, jsonify, current_app


version_bp = Blueprint("version", __name__)


@version_bp.route("", methods=["GET"])
def get_version():
    version = current_app.config.get("VERSION", "0.0.0")
    return jsonify({"version": version}), 200

