"""
GitHub OAuth manager for handling OAuth flow
"""
import requests
import secrets
from typing import Optional, Dict, Tuple
from flask import current_app


class GitHubOAuthManager:
    """Manager for GitHub OAuth operations"""
    
    GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_API_URL = "https://api.github.com/user"
    
    def __init__(self):
        self._states = {}  # Simple in-memory state storage for development
    
    def generate_authorization_url(self) -> Tuple[str, str]:
        """
        Generate GitHub OAuth authorization URL with state parameter
        
        Returns:
            Tuple of (authorization_url, state)
        """
        client_id = current_app.config.get("GITHUB_CLIENT_ID")
        redirect_uri = current_app.config.get("GITHUB_REDIRECT_URI")
        state = secrets.token_urlsafe(32)
        
        # Store state for validation (with simple expiration tracking)
        self._states[state] = True
        
        auth_url = (
            f"{self.GITHUB_AUTHORIZE_URL}"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope=user:email"
            f"&state={state}"
        )
        
        return auth_url, state
    
    def validate_state(self, state: str) -> bool:
        """Validate OAuth state parameter"""
        if state in self._states:
            # Remove state after validation (one-time use)
            del self._states[state]
            return True
        return False
    
    def exchange_code_for_token(self, code: str) -> Optional[str]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from GitHub
            
        Returns:
            Access token or None if exchange fails
        """
        client_id = current_app.config.get("GITHUB_CLIENT_ID")
        client_secret = current_app.config.get("GITHUB_CLIENT_SECRET")
        redirect_uri = current_app.config.get("GITHUB_REDIRECT_URI")
        
        try:
            response = requests.post(
                self.GITHUB_TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
        except requests.RequestException:
            return None
        
        return None
    
    def get_github_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Fetch user information from GitHub API
        
        Args:
            access_token: GitHub access token
            
        Returns:
            User info dict or None if request fails
        """
        try:
            response = requests.get(
                self.GITHUB_USER_API_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Also fetch email if not included in user data
                email = user_data.get("email")
                if not email:
                    email = self._get_primary_email(access_token)
                
                return {
                    "id": user_data.get("id"),
                    "login": user_data.get("login"),
                    "email": email,
                    "name": user_data.get("name"),
                }
        except requests.RequestException:
            return None
        
        return None
    
    def _get_primary_email(self, access_token: str) -> Optional[str]:
        """
        Fetch primary email from GitHub emails API
        
        Args:
            access_token: GitHub access token
            
        Returns:
            Primary email or None
        """
        try:
            response = requests.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                emails = response.json()
                # Find primary email
                for email_data in emails:
                    if email_data.get("primary") and email_data.get("verified"):
                        return email_data.get("email")
                # If no primary, return first verified email
                for email_data in emails:
                    if email_data.get("verified"):
                        return email_data.get("email")
        except requests.RequestException:
            pass
        
        return None
