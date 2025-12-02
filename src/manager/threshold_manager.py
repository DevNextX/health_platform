"""
Threshold configuration manager layer.
Handles validation, draft creation, publishing, and preview of threshold configs.
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from ..extensions import db
from ..models import ThresholdConfig, ThresholdAuditLog, HealthRecord
from ..resilience.policy import db_breaker, with_retry
from ..timeutil import UTC

# Hard safety bounds that cannot be exceeded
SAFETY_BOUNDS = {
    "systolic_min": 30,
    "systolic_max": 250,
    "diastolic_min": 30,
    "diastolic_max": 250,
    "heart_rate_min": 30,
    "heart_rate_max": 150,
}

# Default healthy ranges
DEFAULT_CONFIG = {
    "systolic_min": 90,
    "systolic_max": 120,
    "diastolic_min": 60,
    "diastolic_max": 90,
    "heart_rate_min": 60,
    "heart_rate_max": 90,
}


class ThresholdManager:
    """Manager for threshold configuration operations."""

    def validate_config(self, config: Dict[str, int]) -> Tuple[bool, List[str]]:
        """Validate threshold configuration.

        Args:
            config: Dictionary with systolic_min, systolic_max, diastolic_min,
                   diastolic_max, heart_rate_min, heart_rate_max

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        required_fields = [
            "systolic_min", "systolic_max",
            "diastolic_min", "diastolic_max",
            "heart_rate_min", "heart_rate_max"
        ]

        # Check required fields
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(config[field], int):
                errors.append(f"{field} must be an integer")

        if errors:
            return False, errors

        # Validate ranges: min < max
        for prefix in ["systolic", "diastolic", "heart_rate"]:
            min_key = f"{prefix}_min"
            max_key = f"{prefix}_max"
            if config[min_key] >= config[max_key]:
                errors.append(f"{min_key} must be less than {max_key}")

        # Validate within safety bounds
        # For systolic: must be within 30-250
        if not (SAFETY_BOUNDS["systolic_min"] <= config["systolic_min"] <= SAFETY_BOUNDS["systolic_max"]):
            errors.append(f"systolic_min must be between {SAFETY_BOUNDS['systolic_min']}-{SAFETY_BOUNDS['systolic_max']}")
        if not (SAFETY_BOUNDS["systolic_min"] <= config["systolic_max"] <= SAFETY_BOUNDS["systolic_max"]):
            errors.append(f"systolic_max must be between {SAFETY_BOUNDS['systolic_min']}-{SAFETY_BOUNDS['systolic_max']}")

        # For diastolic: must be within 30-250
        if not (SAFETY_BOUNDS["diastolic_min"] <= config["diastolic_min"] <= SAFETY_BOUNDS["diastolic_max"]):
            errors.append(f"diastolic_min must be between {SAFETY_BOUNDS['diastolic_min']}-{SAFETY_BOUNDS['diastolic_max']}")
        if not (SAFETY_BOUNDS["diastolic_min"] <= config["diastolic_max"] <= SAFETY_BOUNDS["diastolic_max"]):
            errors.append(f"diastolic_max must be between {SAFETY_BOUNDS['diastolic_min']}-{SAFETY_BOUNDS['diastolic_max']}")

        # For heart_rate: must be within 30-150
        if not (SAFETY_BOUNDS["heart_rate_min"] <= config["heart_rate_min"] <= SAFETY_BOUNDS["heart_rate_max"]):
            errors.append(f"heart_rate_min must be between {SAFETY_BOUNDS['heart_rate_min']}-{SAFETY_BOUNDS['heart_rate_max']}")
        if not (SAFETY_BOUNDS["heart_rate_min"] <= config["heart_rate_max"] <= SAFETY_BOUNDS["heart_rate_max"]):
            errors.append(f"heart_rate_max must be between {SAFETY_BOUNDS['heart_rate_min']}-{SAFETY_BOUNDS['heart_rate_max']}")

        return len(errors) == 0, errors

    @db_breaker
    @with_retry()
    def create_draft(self, config: Dict[str, int], user_id: int) -> ThresholdConfig:
        """Create a new draft threshold configuration.

        Args:
            config: Validated configuration dictionary
            user_id: ID of the super admin creating the draft

        Returns:
            Created ThresholdConfig object
        """
        # Get the next version number
        latest = ThresholdConfig.query.order_by(ThresholdConfig.version.desc()).first()
        next_version = (latest.version + 1) if latest else 1

        tc = ThresholdConfig()
        tc.config = json.dumps(config)
        tc.version = next_version
        tc.status = "draft"
        tc.created_by_user_id = user_id

        db.session.add(tc)
        db.session.commit()

        # Create audit log
        audit = ThresholdAuditLog()
        audit.config_id = tc.id
        audit.action = "created"
        audit.operator_user_id = user_id
        audit.old_config = None
        audit.new_config = tc.config
        db.session.add(audit)
        db.session.commit()

        return tc

    @db_breaker
    @with_retry()
    def publish_config(self, config_id: int, user_id: int) -> ThresholdConfig:
        """Publish a draft configuration, making it active.

        This deactivates any currently active config and activates the specified draft.

        Args:
            config_id: ID of the draft config to publish
            user_id: ID of the super admin publishing

        Returns:
            The published ThresholdConfig object

        Raises:
            ValueError: If config not found or not a draft
        """
        tc = db.session.get(ThresholdConfig, config_id)
        if not tc:
            raise ValueError("Configuration not found")
        if tc.status != "draft":
            raise ValueError("Only draft configurations can be published")

        # Get current active config for audit
        current_active = ThresholdConfig.query.filter_by(status="active").first()
        old_config_json = current_active.config if current_active else None

        # Deactivate all other active configs
        ThresholdConfig.query.filter(
            ThresholdConfig.status == "active"
        ).update({"status": "inactive"})

        # Activate this config
        tc.status = "active"
        tc.published_at = datetime.now(UTC)

        # Create audit log
        audit = ThresholdAuditLog()
        audit.config_id = tc.id
        audit.action = "published"
        audit.operator_user_id = user_id
        audit.old_config = old_config_json
        audit.new_config = tc.config
        db.session.add(audit)

        db.session.commit()
        return tc

    @db_breaker
    def get_active_config(self) -> Optional[Dict[str, Any]]:
        """Get the currently active threshold configuration.

        Returns:
            Dictionary with config values and metadata, or default config if none active
        """
        tc = ThresholdConfig.query.filter_by(status="active").first()
        if tc:
            return {
                "id": tc.id,
                "config": json.loads(tc.config),
                "version": tc.version,
                "published_at": tc.published_at,
            }
        # Return default config if none is active
        return {
            "id": None,
            "config": DEFAULT_CONFIG.copy(),
            "version": 0,
            "published_at": None,
        }

    @db_breaker
    def get_draft_config(self) -> Optional[Dict[str, Any]]:
        """Get the latest draft configuration if any.

        Returns:
            Dictionary with config values and metadata, or None if no draft
        """
        tc = ThresholdConfig.query.filter_by(status="draft").order_by(
            ThresholdConfig.version.desc()
        ).first()
        if tc:
            return {
                "id": tc.id,
                "config": json.loads(tc.config),
                "version": tc.version,
                "created_at": tc.created_at,
            }
        return None

    @db_breaker
    def preview_impact(self, config: Dict[str, int]) -> Dict[str, Any]:
        """Preview the impact of a threshold configuration on existing data.

        Analyzes all health records and categorizes them based on the new thresholds.

        Args:
            config: The threshold configuration to preview

        Returns:
            Dictionary with counts for healthy, borderline, and abnormal records
        """
        # Fetch all records (limit to recent 1000 for performance)
        records = HealthRecord.query.order_by(HealthRecord.timestamp.desc()).limit(1000).all()

        healthy = 0
        borderline = 0
        abnormal = 0

        for rec in records:
            status = self._classify_record(rec, config)
            if status == "healthy":
                healthy += 1
            elif status == "borderline":
                borderline += 1
            else:
                abnormal += 1

        total = len(records)
        return {
            "total": total,
            "healthy": healthy,
            "borderline": borderline,
            "abnormal": abnormal,
            "healthy_pct": round(healthy / total * 100, 1) if total else 0,
            "borderline_pct": round(borderline / total * 100, 1) if total else 0,
            "abnormal_pct": round(abnormal / total * 100, 1) if total else 0,
        }

    def _classify_record(self, rec: HealthRecord, config: Dict[str, int]) -> str:
        """Classify a health record based on threshold config.

        Returns: 'healthy', 'borderline', or 'abnormal'
        """
        systolic_min = config["systolic_min"]
        systolic_max = config["systolic_max"]
        diastolic_min = config["diastolic_min"]
        diastolic_max = config["diastolic_max"]
        hr_min = config["heart_rate_min"]
        hr_max = config["heart_rate_max"]

        # Check if values are within healthy range
        sys_healthy = systolic_min <= rec.systolic <= systolic_max
        dia_healthy = diastolic_min <= rec.diastolic <= diastolic_max
        hr_healthy = rec.heart_rate is None or (hr_min <= rec.heart_rate <= hr_max)

        if sys_healthy and dia_healthy and hr_healthy:
            return "healthy"

        # Check for borderline (within 10% of threshold boundaries)
        def is_borderline(val, min_t, max_t):
            margin = (max_t - min_t) * 0.2  # 20% margin
            if val < min_t:
                return val >= min_t - margin
            if val > max_t:
                return val <= max_t + margin
            return True  # within range

        sys_border = is_borderline(rec.systolic, systolic_min, systolic_max)
        dia_border = is_borderline(rec.diastolic, diastolic_min, diastolic_max)
        hr_border = rec.heart_rate is None or is_borderline(rec.heart_rate, hr_min, hr_max)

        if sys_border and dia_border and hr_border:
            return "borderline"

        return "abnormal"

    @db_breaker
    def get_audit_logs(self, page: int = 1, size: int = 20) -> Tuple[int, List[Dict[str, Any]]]:
        """Get paginated audit logs.

        Args:
            page: Page number (1-indexed)
            size: Items per page

        Returns:
            Tuple of (total_count, list_of_audit_log_dicts)
        """
        from ..models import User

        query = ThresholdAuditLog.query.order_by(ThresholdAuditLog.created_at.desc())
        total = query.count()
        logs = query.offset((page - 1) * size).limit(size).all()

        result = []
        for log in logs:
            user = db.session.get(User, log.operator_user_id)
            result.append({
                "id": log.id,
                "config_id": log.config_id,
                "action": log.action,
                "operator": {
                    "id": user.id if user else None,
                    "username": user.username if user else "Unknown",
                    "email": user.email if user else None,
                },
                "old_config": json.loads(log.old_config) if log.old_config else None,
                "new_config": json.loads(log.new_config),
                "created_at": log.created_at,
            })

        return total, result

    @db_breaker
    @with_retry()
    def ensure_default_config(self, user_id: int) -> ThresholdConfig:
        """Ensure a default active configuration exists.

        If no active config exists, creates and publishes the default config.

        Args:
            user_id: ID of the user (typically super admin) initializing

        Returns:
            The active ThresholdConfig
        """
        active = ThresholdConfig.query.filter_by(status="active").first()
        if active:
            return active

        # Create default config
        tc = ThresholdConfig()
        tc.config = json.dumps(DEFAULT_CONFIG)
        tc.version = 1
        tc.status = "active"
        tc.created_by_user_id = user_id
        tc.published_at = datetime.now(UTC)

        db.session.add(tc)
        db.session.commit()

        # Create audit log
        audit = ThresholdAuditLog()
        audit.config_id = tc.id
        audit.action = "created"
        audit.operator_user_id = user_id
        audit.old_config = None
        audit.new_config = tc.config
        db.session.add(audit)
        db.session.commit()

        return tc
