"""
WeChat authentication manager. Handles WeChat Open Platform integration.
"""
import os
import requests
from typing import Optional, Dict, Any
from flask import current_app


class WeChatManager:
    """Manager for WeChat Open Platform authentication"""
    
    # WeChat API endpoints
    QRCONNECT_URL = "https://open.weixin.qq.com/connect/qrconnect"
    ACCESS_TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token"
    USERINFO_URL = "https://api.weixin.qq.com/sns/userinfo"
    
    def __init__(self):
        self.app_id = os.getenv("WECHAT_APP_ID")
        self.app_secret = os.getenv("WECHAT_APP_SECRET")
        self.redirect_uri = os.getenv("WECHAT_REDIRECT_URI")
    
    def get_qrcode_url(self, state: str) -> str:
        """
        Generate WeChat QR code URL for login
        
        Args:
            state: Random state string to prevent CSRF attacks
            
        Returns:
            URL string for WeChat QR code login page
        """
        if not self.app_id or not self.redirect_uri:
            raise ValueError("WeChat configuration missing")
        
        params = {
            "appid": self.app_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "snsapi_login",
            "state": state,
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.QRCONNECT_URL}?{query_string}#wechat_redirect"
    
    def get_access_token(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from WeChat callback
            
        Returns:
            Dictionary containing access_token, openid, and other info
            None if request fails
        """
        if not self.app_id or not self.app_secret:
            raise ValueError("WeChat configuration missing")
        
        params = {
            "appid": self.app_id,
            "secret": self.app_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
        
        try:
            response = requests.get(self.ACCESS_TOKEN_URL, params=params, timeout=10)
            data = response.json()
            
            # Check for errors
            if "errcode" in data:
                current_app.logger.error(f"WeChat access token error: {data}")
                return None
            
            return data
        except Exception as e:
            current_app.logger.error(f"WeChat access token request failed: {e}")
            return None
    
    def get_user_info(self, access_token: str, openid: str) -> Optional[Dict[str, Any]]:
        """
        Get WeChat user information
        
        Args:
            access_token: Access token from WeChat
            openid: User's unique OpenID
            
        Returns:
            Dictionary containing user info (nickname, headimgurl, etc.)
            None if request fails
        """
        params = {
            "access_token": access_token,
            "openid": openid,
        }
        
        try:
            response = requests.get(self.USERINFO_URL, params=params, timeout=10)
            data = response.json()
            
            # Check for errors
            if "errcode" in data:
                current_app.logger.error(f"WeChat userinfo error: {data}")
                return None
            
            return data
        except Exception as e:
            current_app.logger.error(f"WeChat userinfo request failed: {e}")
            return None
