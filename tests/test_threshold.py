"""
Test cases for threshold configuration endpoints.
"""
import json
import pytest
from src.manager.user_manager import UserManager
from src.manager.threshold_manager import ThresholdManager, DEFAULT_CONFIG, SAFETY_BOUNDS


def login(client, email, password):
    return client.post('/api/v1/auth/login', json={'email': email, 'password': password})


# Test fixture: valid threshold configuration
VALID_THRESHOLD_CONFIG = {
    "systolic_min": 90,
    "systolic_max": 120,
    "diastolic_min": 60,
    "diastolic_max": 90,
    "heart_rate_min": 60,
    "heart_rate_max": 90,
}


class TestThresholdManager:
    """Test threshold manager validation logic."""

    def test_validate_config_valid(self, app):
        """Test validation with valid config."""
        with app.app_context():
            tm = ThresholdManager()
            is_valid, errors = tm.validate_config(VALID_THRESHOLD_CONFIG.copy())
            assert is_valid is True
            assert len(errors) == 0

    def test_validate_config_missing_fields(self, app):
        """Test validation with missing fields."""
        with app.app_context():
            tm = ThresholdManager()
            config = {"systolic_min": 90}
            is_valid, errors = tm.validate_config(config)
            assert is_valid is False
            assert any("systolic_max" in e for e in errors)

    def test_validate_config_min_greater_than_max(self, app):
        """Test validation when min >= max."""
        with app.app_context():
            tm = ThresholdManager()
            config = {
                "systolic_min": 130,
                "systolic_max": 120,  # min > max
                "diastolic_min": 60,
                "diastolic_max": 90,
                "heart_rate_min": 60,
                "heart_rate_max": 90,
            }
            is_valid, errors = tm.validate_config(config)
            assert is_valid is False
            assert any("systolic_min must be less than systolic_max" in e for e in errors)

    def test_validate_config_outside_safety_bounds(self, app):
        """Test validation with values outside safety bounds."""
        with app.app_context():
            tm = ThresholdManager()
            config = {
                "systolic_min": 20,  # below 30
                "systolic_max": 260,  # above 250
                "diastolic_min": 60,
                "diastolic_max": 90,
                "heart_rate_min": 20,  # below 30
                "heart_rate_max": 160,  # above 150
            }
            is_valid, errors = tm.validate_config(config)
            assert is_valid is False
            assert len(errors) >= 4  # multiple bound violations


class TestThresholdAPI:
    """Test threshold configuration API endpoints."""

    def test_get_active_thresholds_default(self, client, auth_headers):
        """Test getting active thresholds returns default when none configured."""
        access_headers = auth_headers['access']
        resp = client.get('/api/v1/superadmin/thresholds/active', headers=access_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'config' in data
        assert data['config']['systolic_min'] == DEFAULT_CONFIG['systolic_min']
        assert 'safety_bounds' in data

    def test_create_draft_requires_super_admin(self, client, auth_headers):
        """Test that creating a draft requires SUPER_ADMIN role."""
        access_headers = auth_headers['access']
        resp = client.post('/api/v1/superadmin/thresholds/draft', json=VALID_THRESHOLD_CONFIG, headers=access_headers)
        assert resp.status_code == 403

    def test_super_admin_create_draft(self, client):
        """Test SUPER_ADMIN can create draft threshold config."""
        um = UserManager()
        # Create and login super admin
        client.post('/api/v1/auth/register', json={
            'username': 'superadmin', 'email': 'sa@example.com', 'password': 'Password123'
        })
        sa = um.get_user_by_email('sa@example.com')
        um.set_role(sa, 'SUPER_ADMIN')

        sa_login = login(client, 'sa@example.com', 'Password123')
        assert sa_login.status_code == 200
        sa_access = {'Authorization': f"Bearer {sa_login.get_json()['access_token']}"}

        # Create draft with custom values
        custom_config = {
            "systolic_min": 85,
            "systolic_max": 130,
            "diastolic_min": 55,
            "diastolic_max": 85,
            "heart_rate_min": 55,
            "heart_rate_max": 100,
        }
        resp = client.post('/api/v1/superadmin/thresholds/draft', json=custom_config, headers=sa_access)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'draft'
        assert data['config']['systolic_min'] == 85

    def test_super_admin_publish_draft(self, client):
        """Test SUPER_ADMIN can publish draft threshold config."""
        um = UserManager()
        # Create and login super admin
        client.post('/api/v1/auth/register', json={
            'username': 'superadmin', 'email': 'sa2@example.com', 'password': 'Password123'
        })
        sa = um.get_user_by_email('sa2@example.com')
        um.set_role(sa, 'SUPER_ADMIN')

        sa_login = login(client, 'sa2@example.com', 'Password123')
        sa_access = {'Authorization': f"Bearer {sa_login.get_json()['access_token']}"}

        # Create draft
        draft_resp = client.post('/api/v1/superadmin/thresholds/draft', json={
            "systolic_min": 85,
            "systolic_max": 130,
            "diastolic_min": 55,
            "diastolic_max": 85,
            "heart_rate_min": 55,
            "heart_rate_max": 100,
        }, headers=sa_access)
        draft_id = draft_resp.get_json()['id']

        # Publish
        pub_resp = client.post(f'/api/v1/superadmin/thresholds/{draft_id}/publish', headers=sa_access)
        assert pub_resp.status_code == 200
        data = pub_resp.get_json()
        assert data['status'] == 'active'
        assert data['published_at'] is not None

        # Verify active config changed
        active_resp = client.get('/api/v1/superadmin/thresholds/active', headers=sa_access)
        active_data = active_resp.get_json()
        assert active_data['config']['systolic_min'] == 85

    def test_super_admin_preview_impact(self, client):
        """Test preview impact calculation."""
        um = UserManager()
        # Create and login super admin
        client.post('/api/v1/auth/register', json={
            'username': 'superadmin', 'email': 'sa3@example.com', 'password': 'Password123'
        })
        sa = um.get_user_by_email('sa3@example.com')
        um.set_role(sa, 'SUPER_ADMIN')

        sa_login = login(client, 'sa3@example.com', 'Password123')
        sa_access = {'Authorization': f"Bearer {sa_login.get_json()['access_token']}"}

        # Create some health records first
        client.post('/api/v1/health', json={
            'systolic': 100, 'diastolic': 70, 'heart_rate': 75
        }, headers=sa_access)
        client.post('/api/v1/health', json={
            'systolic': 150, 'diastolic': 95, 'heart_rate': 90
        }, headers=sa_access)

        # Preview impact
        resp = client.post('/api/v1/superadmin/thresholds/preview', json={
            "systolic_min": 90,
            "systolic_max": 120,
            "diastolic_min": 60,
            "diastolic_max": 80,
            "heart_rate_min": 60,
            "heart_rate_max": 80,
        }, headers=sa_access)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'total' in data
        assert 'healthy' in data
        assert 'abnormal' in data
        assert data['total'] >= 2

    def test_validation_error_on_invalid_config(self, client):
        """Test validation errors are returned for invalid configs."""
        um = UserManager()
        client.post('/api/v1/auth/register', json={
            'username': 'superadmin', 'email': 'sa4@example.com', 'password': 'Password123'
        })
        sa = um.get_user_by_email('sa4@example.com')
        um.set_role(sa, 'SUPER_ADMIN')

        sa_login = login(client, 'sa4@example.com', 'Password123')
        sa_access = {'Authorization': f"Bearer {sa_login.get_json()['access_token']}"}

        # Invalid config: min > max
        resp = client.post('/api/v1/superadmin/thresholds/draft', json={
            "systolic_min": 130,
            "systolic_max": 90,  # Invalid
            "diastolic_min": 60,
            "diastolic_max": 90,
            "heart_rate_min": 60,
            "heart_rate_max": 90,
        }, headers=sa_access)
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'details' in data

    def test_audit_logs_created_on_draft(self, client):
        """Test audit logs are created when draft is created."""
        um = UserManager()
        client.post('/api/v1/auth/register', json={
            'username': 'superadmin', 'email': 'sa5@example.com', 'password': 'Password123'
        })
        sa = um.get_user_by_email('sa5@example.com')
        um.set_role(sa, 'SUPER_ADMIN')

        sa_login = login(client, 'sa5@example.com', 'Password123')
        sa_access = {'Authorization': f"Bearer {sa_login.get_json()['access_token']}"}

        # Create draft
        client.post('/api/v1/superadmin/thresholds/draft', json=VALID_THRESHOLD_CONFIG, headers=sa_access)

        # Check audit logs
        logs_resp = client.get('/api/v1/superadmin/thresholds/audit-logs', headers=sa_access)
        assert logs_resp.status_code == 200
        data = logs_resp.get_json()
        assert len(data['logs']) >= 1
        assert data['logs'][0]['action'] == 'created'

    def test_reset_to_default(self, client):
        """Test reset creates draft with default values."""
        um = UserManager()
        client.post('/api/v1/auth/register', json={
            'username': 'superadmin', 'email': 'sa6@example.com', 'password': 'Password123'
        })
        sa = um.get_user_by_email('sa6@example.com')
        um.set_role(sa, 'SUPER_ADMIN')

        sa_login = login(client, 'sa6@example.com', 'Password123')
        sa_access = {'Authorization': f"Bearer {sa_login.get_json()['access_token']}"}

        # Reset to default
        resp = client.post('/api/v1/superadmin/thresholds/reset', headers=sa_access)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'draft'
        assert data['config']['systolic_min'] == DEFAULT_CONFIG['systolic_min']
        assert data['config']['systolic_max'] == DEFAULT_CONFIG['systolic_max']

    def test_export_audit_logs_csv(self, client):
        """Test export audit logs as CSV."""
        um = UserManager()
        client.post('/api/v1/auth/register', json={
            'username': 'superadmin', 'email': 'sa7@example.com', 'password': 'Password123'
        })
        sa = um.get_user_by_email('sa7@example.com')
        um.set_role(sa, 'SUPER_ADMIN')

        sa_login = login(client, 'sa7@example.com', 'Password123')
        sa_access = {'Authorization': f"Bearer {sa_login.get_json()['access_token']}"}

        # Create a draft to have at least one audit log
        client.post('/api/v1/superadmin/thresholds/draft', json=VALID_THRESHOLD_CONFIG, headers=sa_access)

        # Export CSV
        resp = client.get('/api/v1/superadmin/thresholds/audit-logs/export', headers=sa_access)
        assert resp.status_code == 200
        assert 'text/csv' in resp.content_type
        assert 'Content-Disposition' in resp.headers
