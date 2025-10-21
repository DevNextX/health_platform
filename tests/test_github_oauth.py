"""
Test cases for GitHub OAuth authentication endpoints
"""
import pytest
from unittest.mock import patch, MagicMock
from src.manager.user_manager import UserManager


class TestGitHubOAuthEndpoints:
    """Test GitHub OAuth authentication endpoints"""
    
    def test_github_login_redirect(self, client):
        """Test GitHub login initiates redirect"""
        response = client.get('/api/v1/auth/github/login')
        assert response.status_code == 302
        assert 'github.com' in response.location
        assert 'client_id' in response.location
        assert 'state' in response.location
    
    @patch('src.service.github_auth_service.github_oauth_manager.exchange_code_for_token')
    @patch('src.service.github_auth_service.github_oauth_manager.get_github_user_info')
    def test_github_callback_new_user(self, mock_get_user, mock_exchange_token, client, app):
        """Test GitHub callback creates new user"""
        # Mock GitHub API responses
        mock_exchange_token.return_value = 'mock_access_token'
        mock_get_user.return_value = {
            'id': 12345,
            'login': 'testuser',
            'email': 'testuser@github.com',
            'name': 'Test User'
        }
        
        # First, initiate login to set state in session
        with client.session_transaction() as sess:
            sess['github_oauth_state'] = 'test_state_123'
        
        # Simulate callback
        response = client.get('/api/v1/auth/github/callback?code=test_code&state=test_state_123')
        
        assert response.status_code == 302
        assert 'access_token' in response.location
        assert 'refresh_token' in response.location
        
        # Verify user was created
        user_manager = UserManager()
        user = user_manager.get_user_by_github_id(12345)
        assert user is not None
        assert user.github_username == 'testuser'
        assert user.email == 'testuser@github.com'
    
    @patch('src.service.github_auth_service.github_oauth_manager.exchange_code_for_token')
    @patch('src.service.github_auth_service.github_oauth_manager.get_github_user_info')
    def test_github_callback_existing_user_by_email(self, mock_get_user, mock_exchange_token, client, app):
        """Test GitHub callback links to existing user by email"""
        # Create existing user
        user_manager = UserManager()
        existing_user = user_manager.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )
        
        # Mock GitHub API responses with same email
        mock_exchange_token.return_value = 'mock_access_token'
        mock_get_user.return_value = {
            'id': 99999,
            'login': 'githubuser',
            'email': 'existing@example.com',
            'name': 'GitHub User'
        }
        
        with client.session_transaction() as sess:
            sess['github_oauth_state'] = 'test_state_456'
        
        response = client.get('/api/v1/auth/github/callback?code=test_code&state=test_state_456')
        
        assert response.status_code == 302
        
        # Verify user was linked
        user = user_manager.get_user_by_github_id(99999)
        assert user is not None
        assert user.id == existing_user.id
        assert user.github_username == 'githubuser'
    
    @patch('src.service.github_auth_service.github_oauth_manager.exchange_code_for_token')
    @patch('src.service.github_auth_service.github_oauth_manager.get_github_user_info')
    def test_github_callback_existing_github_user(self, mock_get_user, mock_exchange_token, client, app):
        """Test GitHub callback for user who already linked GitHub"""
        # Create user with GitHub account
        user_manager = UserManager()
        existing_user = user_manager.create_user_from_github(
            username='githubuser',
            email='github@example.com',
            github_id=55555,
            github_username='githubuser'
        )
        
        # Mock GitHub API responses
        mock_exchange_token.return_value = 'mock_access_token'
        mock_get_user.return_value = {
            'id': 55555,
            'login': 'githubuser',
            'email': 'github@example.com',
            'name': 'GitHub User'
        }
        
        with client.session_transaction() as sess:
            sess['github_oauth_state'] = 'test_state_789'
        
        response = client.get('/api/v1/auth/github/callback?code=test_code&state=test_state_789')
        
        assert response.status_code == 302
        assert 'access_token' in response.location
    
    def test_github_callback_invalid_state(self, client):
        """Test GitHub callback with invalid state"""
        with client.session_transaction() as sess:
            sess['github_oauth_state'] = 'correct_state'
        
        response = client.get('/api/v1/auth/github/callback?code=test_code&state=wrong_state')
        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid OAuth state' in data['message']
    
    def test_github_callback_missing_code(self, client):
        """Test GitHub callback without code parameter"""
        with client.session_transaction() as sess:
            sess['github_oauth_state'] = 'test_state'
        
        response = client.get('/api/v1/auth/github/callback?state=test_state')
        assert response.status_code == 400
    
    def test_github_callback_user_cancelled(self, client):
        """Test GitHub callback when user cancels"""
        response = client.get('/api/v1/auth/github/callback?error=access_denied')
        assert response.status_code == 302
        assert 'error=github_cancelled' in response.location
    
    @patch('src.service.github_auth_service.github_oauth_manager.exchange_code_for_token')
    @patch('src.service.github_auth_service.github_oauth_manager.get_github_user_info')
    def test_github_callback_no_email(self, mock_get_user, mock_exchange_token, client):
        """Test GitHub callback when email is private"""
        mock_exchange_token.return_value = 'mock_access_token'
        mock_get_user.return_value = {
            'id': 77777,
            'login': 'privateuser',
            'email': None,
            'name': 'Private User'
        }
        
        with client.session_transaction() as sess:
            sess['github_oauth_state'] = 'test_state_private'
        
        response = client.get('/api/v1/auth/github/callback?code=test_code&state=test_state_private')
        
        assert response.status_code == 302
        assert 'complete-registration' in response.location
    
    def test_github_complete_registration_success(self, client):
        """Test completing registration with email"""
        # Set pending GitHub info in session
        with client.session_transaction() as sess:
            sess['github_pending'] = {
                'github_id': 88888,
                'github_username': 'pendinguser',
                'name': 'Pending User'
            }
        
        response = client.post('/api/v1/auth/github/complete', json={
            'email': 'pending@example.com'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        
        # Verify user was created
        user_manager = UserManager()
        user = user_manager.get_user_by_github_id(88888)
        assert user is not None
        assert user.email == 'pending@example.com'
    
    def test_github_complete_registration_no_session(self, client):
        """Test completing registration without session data"""
        response = client.post('/api/v1/auth/github/complete', json={
            'email': 'test@example.com'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'No pending GitHub registration' in data['message']
    
    def test_github_complete_registration_missing_email(self, client):
        """Test completing registration without email"""
        with client.session_transaction() as sess:
            sess['github_pending'] = {
                'github_id': 99999,
                'github_username': 'testuser',
                'name': 'Test User'
            }
        
        response = client.post('/api/v1/auth/github/complete', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Email is required' in data['message']
    
    def test_github_complete_registration_duplicate_email(self, client):
        """Test completing registration with existing email"""
        # Create existing user
        user_manager = UserManager()
        user_manager.create_user(
            username='existing',
            email='duplicate@example.com',
            password='password123'
        )
        
        with client.session_transaction() as sess:
            sess['github_pending'] = {
                'github_id': 11111,
                'github_username': 'newuser',
                'name': 'New User'
            }
        
        response = client.post('/api/v1/auth/github/complete', json={
            'email': 'duplicate@example.com'
        })
        
        # Should link to existing user or return 409
        # Check both possibilities
        if response.status_code == 409:
            data = response.get_json()
            assert 'already' in data['message'].lower()
        else:
            # User was linked
            assert response.status_code == 200
