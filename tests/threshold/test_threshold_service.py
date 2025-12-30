import json
import pytest
from src.service.threshold_service import bp as threshold_bp


def test_routes_exist_with_auth(client, super_admin_headers):
    """Test that threshold routes exist and require proper authentication."""
    # Test draft creation (requires SUPER_ADMIN)
    res = client.post('/api/v1/admin/thresholds/draft', 
                      json={
                          "systolic_healthy": [90, 120],
                          "systolic_borderline": [120, 140],
                          "diastolic_healthy": [60, 80],
                          "diastolic_borderline": [80, 90],
                          "systolic_min": 90,
                          "systolic_max": 140,
                          "diastolic_min": 60,
                          "diastolic_max": 90
                      },
                      headers=super_admin_headers)
    # Should be 201 (created) or 400 (validation error)
    assert res.status_code in (201, 400), f"Unexpected status: {res.status_code}, {res.get_json()}"
    
    # Test active profile endpoint (requires auth but any role)
    res = client.get('/api/v1/thresholds/active', headers=super_admin_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert "version" in data


def test_routes_require_auth(client):
    """Test that routes reject unauthenticated requests."""
    # No JWT token provided
    res = client.post('/api/v1/admin/thresholds/draft', json={})
    assert res.status_code == 401
    
    res = client.get('/api/v1/thresholds/active')
    assert res.status_code == 401
