"""
Test cases for WeChat authentication endpoints.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from src.manager.user_manager import UserManager


class TestWeChatAuth:
    """Test WeChat authentication functionality"""
    
    @patch('src.manager.wechat_manager.WeChatManager.get_qrcode_url')
    def test_wechat_login_success(self, mock_get_qrcode_url, client):
        """Test WeChat login QR code generation"""
        mock_get_qrcode_url.return_value = "https://open.weixin.qq.com/connect/qrconnect?appid=test&state=test_state"
        
        response = client.get('/api/v1/auth/wechat/login')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'qrcode_url' in data
        assert 'state' in data
        assert len(data['state']) > 0
    
    @patch('src.manager.wechat_manager.WeChatManager.get_access_token')
    def test_wechat_callback_new_user(self, mock_get_access_token, client):
        """Test WeChat callback for a new user"""
        # First get a state
        with patch('src.manager.wechat_manager.WeChatManager.get_qrcode_url') as mock_qr:
            mock_qr.return_value = "https://test.url"
            qr_response = client.get('/api/v1/auth/wechat/login')
            state = qr_response.get_json()['state']
        
        # Mock WeChat access token response
        mock_get_access_token.return_value = {
            'access_token': 'test_access_token',
            'openid': 'test_openid_123'
        }
        
        # Send callback with code
        callback_data = {
            'code': 'test_auth_code',
            'state': state
        }
        
        response = client.post('/api/v1/auth/wechat/callback', json=callback_data)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'new_user'
        assert data['state'] == state
        assert 'Please bind your email' in data['message']
    
    @patch('src.manager.wechat_manager.WeChatManager.get_access_token')
    def test_wechat_callback_existing_user(self, mock_get_access_token, client, app):
        """Test WeChat callback for an existing user"""
        # Create a user with WeChat OpenID
        with app.app_context():
            from src.manager.user_manager import UserManager
            user_mgr = UserManager()
            user = user_mgr.create_wechat_user(
                username='wechat_user',
                email='wechat@example.com',
                wechat_openid='existing_openid_456'
            )
            user_id = user.id
        
        # Get a state
        with patch('src.manager.wechat_manager.WeChatManager.get_qrcode_url') as mock_qr:
            mock_qr.return_value = "https://test.url"
            qr_response = client.get('/api/v1/auth/wechat/login')
            state = qr_response.get_json()['state']
        
        # Mock WeChat to return existing openid
        mock_get_access_token.return_value = {
            'access_token': 'test_access_token',
            'openid': 'existing_openid_456'
        }
        
        # Send callback
        callback_data = {
            'code': 'test_auth_code',
            'state': state
        }
        
        response = client.post('/api/v1/auth/wechat/callback', json=callback_data)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'existing_user'
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['token_type'] == 'Bearer'
    
    def test_wechat_callback_invalid_state(self, client):
        """Test WeChat callback with invalid state"""
        callback_data = {
            'code': 'test_auth_code',
            'state': 'invalid_state_12345'
        }
        
        response = client.post('/api/v1/auth/wechat/callback', json=callback_data)
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'Invalid or expired state' in data['message']
    
    def test_wechat_callback_missing_fields(self, client):
        """Test WeChat callback with missing fields"""
        response = client.post('/api/v1/auth/wechat/callback', json={})
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'Missing code or state' in data['message']
    
    @patch('src.manager.wechat_manager.WeChatManager.get_access_token')
    def test_wechat_bind_success(self, mock_get_access_token, client):
        """Test successful WeChat account binding with email"""
        # Setup: get state and simulate callback
        with patch('src.manager.wechat_manager.WeChatManager.get_qrcode_url') as mock_qr:
            mock_qr.return_value = "https://test.url"
            qr_response = client.get('/api/v1/auth/wechat/login')
            state = qr_response.get_json()['state']
        
        mock_get_access_token.return_value = {
            'access_token': 'test_access_token',
            'openid': 'new_openid_789'
        }
        
        callback_response = client.post('/api/v1/auth/wechat/callback', json={
            'code': 'test_auth_code',
            'state': state
        })
        assert callback_response.status_code == 200
        
        # Now bind email
        bind_data = {
            'state': state,
            'username': 'new_wechat_user',
            'email': 'newwechat@example.com',
            'password': 'optional_password123'  # Optional password
        }
        
        response = client.post('/api/v1/auth/wechat/bind', json=bind_data)
        assert response.status_code == 201
        
        data = response.get_json()
        assert data['username'] == 'new_wechat_user'
        assert data['email'] == 'newwechat@example.com'
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'id' in data
    
    @patch('src.manager.wechat_manager.WeChatManager.get_access_token')
    def test_wechat_bind_without_password(self, mock_get_access_token, client):
        """Test WeChat account binding without password (WeChat-only login)"""
        # Setup
        with patch('src.manager.wechat_manager.WeChatManager.get_qrcode_url') as mock_qr:
            mock_qr.return_value = "https://test.url"
            qr_response = client.get('/api/v1/auth/wechat/login')
            state = qr_response.get_json()['state']
        
        mock_get_access_token.return_value = {
            'access_token': 'test_access_token',
            'openid': 'new_openid_999'
        }
        
        client.post('/api/v1/auth/wechat/callback', json={
            'code': 'test_auth_code',
            'state': state
        })
        
        # Bind without password
        bind_data = {
            'state': state,
            'username': 'wechat_only_user',
            'email': 'wechatonly@example.com'
            # No password provided
        }
        
        response = client.post('/api/v1/auth/wechat/bind', json=bind_data)
        assert response.status_code == 201
        
        data = response.get_json()
        assert data['username'] == 'wechat_only_user'
        assert 'access_token' in data
    
    @patch('src.manager.wechat_manager.WeChatManager.get_access_token')
    def test_wechat_bind_duplicate_email(self, mock_get_access_token, client, app):
        """Test WeChat binding with already registered email"""
        # First create a regular user with the email
        with app.app_context():
            user_mgr = UserManager()
            user_mgr.create_user(
                username='existing_user',
                email='existing@example.com',
                password='password123'
            )
        
        # Setup WeChat flow
        with patch('src.manager.wechat_manager.WeChatManager.get_qrcode_url') as mock_qr:
            mock_qr.return_value = "https://test.url"
            qr_response = client.get('/api/v1/auth/wechat/login')
            state = qr_response.get_json()['state']
        
        mock_get_access_token.return_value = {
            'access_token': 'test_access_token',
            'openid': 'test_openid_duplicate'
        }
        
        client.post('/api/v1/auth/wechat/callback', json={
            'code': 'test_auth_code',
            'state': state
        })
        
        # Try to bind with existing email
        bind_data = {
            'state': state,
            'username': 'another_user',
            'email': 'existing@example.com'  # This email already exists
        }
        
        response = client.post('/api/v1/auth/wechat/bind', json=bind_data)
        assert response.status_code == 409
        
        data = response.get_json()
        assert 'Email already exists' in data['message']
    
    def test_wechat_bind_missing_fields(self, client):
        """Test WeChat bind with missing required fields"""
        bind_data = {
            'state': 'some_state',
            'email': 'test@example.com'
            # Missing username
        }
        
        response = client.post('/api/v1/auth/wechat/bind', json=bind_data)
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'Missing required fields' in data['message']
    
    def test_wechat_bind_invalid_state(self, client):
        """Test WeChat bind with invalid state"""
        bind_data = {
            'state': 'invalid_state',
            'username': 'testuser',
            'email': 'test@example.com'
        }
        
        response = client.post('/api/v1/auth/wechat/bind', json=bind_data)
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'Invalid or expired state' in data['message']
