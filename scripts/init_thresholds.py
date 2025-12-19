from src.app import create_app
from src.extensions import db
from src.models import ThresholdConfig, ThresholdAuditLog, User
import json

def init_thresholds():
    app = create_app()
    with app.app_context():
        # Check if tables exist (they should if app is running)
        # Check if any active config exists
        if ThresholdConfig.query.filter_by(status="active").first():
            print("Active threshold config already exists.")
            return

        print("Initializing default threshold config...")
        # Updated payload structure with borderline_max
        payload = {
            "systolic": {"min": 90, "max": 120, "borderline_max": 140},
            "diastolic": {"min": 60, "max": 80, "borderline_max": 90},
            "heart_rate": {"min": 60, "max": 100}
        }
        
        # Find a user to attribute to (Super Admin preferred)
        admin = User.query.filter_by(role="SUPER_ADMIN").first()
        if not admin:
            print("No SUPER_ADMIN found. Trying ADMIN...")
            admin = User.query.filter_by(role="ADMIN").first()
        if not admin:
            print("No ADMIN found. Trying any user...")
            admin = User.query.first()
        
        if not admin:
            print("No users found. Cannot attribute threshold config. Please create a user first.")
            return

        config = ThresholdConfig(
            payload=json.dumps(payload),
            status="active",
            version=1,
            created_by=admin.id
        )
        db.session.add(config)
        
        audit = ThresholdAuditLog(
            action="init_default",
            actor_id=admin.id,
            new_payload=config.payload
        )
        db.session.add(audit)
        db.session.flush()
        
        audit.config_id = config.id
        db.session.commit()
        print(f"Default threshold config initialized (Version 1) by user {admin.username} (ID: {admin.id}).")

if __name__ == "__main__":
    init_thresholds()
