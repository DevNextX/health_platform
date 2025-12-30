import pytest
from src.manager.user_manager import UserManager


def login(client, email, password):
    return client.post('/api/v1/auth/login', json={'email': email, 'password': password})


class TestAdminAPI:
    def test_forbidden_for_user(self, client):
        # Register normal user
        client.post('/api/v1/auth/register', json={
            'username': 'u1', 'email': 'u1@example.com', 'password': 'Password123'
        })
        # Login
        res = login(client, 'u1@example.com', 'Password123')
        assert res.status_code == 200
        access = {'Authorization': f"Bearer {res.get_json()['access_token']}"}
        # Try admin API
        r = client.get('/api/v1/admin/users', headers=access)
        assert r.status_code == 403

    def test_admin_promote_and_reset(self, client):
        um = UserManager()
        # Create super admin
        client.post('/api/v1/auth/register', json={'username': 'sa', 'email': 'sa@example.com', 'password': 'Password123'})
        sa = um.get_user_by_email('sa@example.com')
        um.set_role(sa, 'SUPER_ADMIN')

        # Create target admin and normal user
        client.post('/api/v1/auth/register', json={'username': 'adm', 'email': 'adm@example.com', 'password': 'Password123'})
        client.post('/api/v1/auth/register', json={'username': 'u2', 'email': 'u2@example.com', 'password': 'Password123'})
        adm = um.get_user_by_email('adm@example.com')
        u2 = um.get_user_by_email('u2@example.com')

        # Login as super admin
        sa_login = login(client, 'sa@example.com', 'Password123')
        assert sa_login.status_code == 200
        sa_access = {'Authorization': f"Bearer {sa_login.get_json()['access_token']}"}

        # Promote adm to ADMIN
        r1 = client.post(f'/api/v1/admin/users/{adm.id}/promote-admin', headers=sa_access)
        assert r1.status_code == 200

        # Login as admin and reset u2 password
        adm_login = login(client, 'adm@example.com', 'Password123')
        assert adm_login.status_code == 200
        adm_access = {'Authorization': f"Bearer {adm_login.get_json()['access_token']}"}

        r2 = client.post(f'/api/v1/admin/users/{u2.id}/reset-password', headers=adm_access)
        assert r2.status_code == 200
        temp_pwd = r2.get_json().get('temp_password')
        assert temp_pwd and isinstance(temp_pwd, str)

        # Login as u2 with new password; expect must_change_password True
        u2_login = login(client, 'u2@example.com', temp_pwd)
        assert u2_login.status_code == 200
        assert u2_login.get_json().get('must_change_password') is True
