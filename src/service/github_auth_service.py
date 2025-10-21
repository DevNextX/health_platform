"""
GitHub OAuth service endpoints
"""
from flask import Blueprint, request, jsonify, redirect, session, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import limiter
from ..manager.user_manager import UserManager
from ..manager.member_manager import MemberManager
from ..manager.github_oauth_manager import GitHubOAuthManager
from ..security import make_tokens
from ..utils import error

github_auth_bp = Blueprint("github_auth", __name__)
user_manager = UserManager()
member_manager = MemberManager()
github_oauth_manager = GitHubOAuthManager()


@github_auth_bp.route("/login", methods=["GET"])
@limiter.limit(lambda: current_app.config.get("RATELIMIT_AUTH", "5 per minute"))
def github_login():
    """
    Initiate GitHub OAuth flow
    Redirects user to GitHub authorization page
    """
    auth_url, state = github_oauth_manager.generate_authorization_url()
    
    # Store state in session for validation in callback
    session["github_oauth_state"] = state
    
    return redirect(auth_url)


@github_auth_bp.route("/callback", methods=["GET"])
@limiter.limit(lambda: current_app.config.get("RATELIMIT_AUTH", "5 per minute"))
def github_callback():
    """
    Handle GitHub OAuth callback
    Exchange code for token, fetch user info, create/link account
    """
    code = request.args.get("code")
    state = request.args.get("state")
    error_param = request.args.get("error")
    
    # Handle user cancellation
    if error_param:
        # Redirect to frontend with error message
        frontend_url = current_app.config.get("CORS_ORIGINS", ["http://localhost:3000"])[0]
        return redirect(f"{frontend_url}/login?error=github_cancelled")
    
    # Validate required parameters
    if not code or not state:
        return jsonify(error("400", "Missing code or state parameter")), 400
    
    # Validate state to prevent CSRF
    stored_state = session.get("github_oauth_state")
    if not stored_state or stored_state != state:
        return jsonify(error("400", "Invalid OAuth state")), 400
    
    # Clear state from session
    session.pop("github_oauth_state", None)
    
    # Exchange code for access token
    access_token = github_oauth_manager.exchange_code_for_token(code)
    if not access_token:
        frontend_url = current_app.config.get("CORS_ORIGINS", ["http://localhost:3000"])[0]
        return redirect(f"{frontend_url}/login?error=github_failed")
    
    # Fetch user info from GitHub
    github_user = github_oauth_manager.get_github_user_info(access_token)
    if not github_user or not github_user.get("id") or not github_user.get("login"):
        frontend_url = current_app.config.get("CORS_ORIGINS", ["http://localhost:3000"])[0]
        return redirect(f"{frontend_url}/login?error=github_failed")
    
    github_id = github_user["id"]
    github_username = github_user["login"]
    email = github_user.get("email")
    
    # Handle email privacy scenario
    if not email:
        # Store GitHub info in session for later completion
        session["github_pending"] = {
            "github_id": github_id,
            "github_username": github_username,
            "name": github_user.get("name") or github_username
        }
        frontend_url = current_app.config.get("CORS_ORIGINS", ["http://localhost:3000"])[0]
        return redirect(f"{frontend_url}/login/complete-registration")
    
    # Try to find existing user by GitHub ID or email
    user = user_manager.get_user_by_github_id(github_id)
    
    if not user:
        # Check if user exists by email
        user = user_manager.get_user_by_email(email)
        
        if user:
            # Link GitHub account to existing user
            try:
                user = user_manager.link_github_account(user, github_id, github_username)
            except ValueError:
                frontend_url = current_app.config.get("CORS_ORIGINS", ["http://localhost:3000"])[0]
                return redirect(f"{frontend_url}/login?error=github_failed")
        else:
            # Create new user
            username = github_user.get("name") or github_username
            try:
                user = user_manager.create_user_from_github(
                    username=username,
                    email=email,
                    github_id=github_id,
                    github_username=github_username
                )
            except ValueError:
                frontend_url = current_app.config.get("CORS_ORIGINS", ["http://localhost:3000"])[0]
                return redirect(f"{frontend_url}/login?error=email_exists")
    
    # Generate JWT tokens
    tokens = make_tokens(identity=user.id, token_version=user.token_version)
    
    # Redirect to frontend with tokens
    frontend_url = current_app.config.get("CORS_ORIGINS", ["http://localhost:3000"])[0]
    return redirect(
        f"{frontend_url}/login/callback"
        f"?access_token={tokens['access_token']}"
        f"&refresh_token={tokens['refresh_token']}"
    )


@github_auth_bp.route("/complete", methods=["POST"])
@limiter.limit(lambda: current_app.config.get("RATELIMIT_AUTH", "5 per minute"))
def github_complete_registration():
    """
    Complete GitHub registration when email is private
    User provides email manually
    """
    data = request.get_json(force=True) or {}
    email = data.get("email")
    
    if not email:
        return jsonify(error("400", "Email is required")), 400
    
    # Get pending GitHub info from session
    github_pending = session.get("github_pending")
    if not github_pending:
        return jsonify(error("400", "No pending GitHub registration")), 400
    
    github_id = github_pending.get("github_id")
    github_username = github_pending.get("github_username")
    username = github_pending.get("name")
    
    if not github_id or not github_username:
        return jsonify(error("400", "Invalid session data")), 400
    
    # Clear pending data
    session.pop("github_pending", None)
    
    # Try to find existing user by GitHub ID or email
    user = user_manager.get_user_by_github_id(github_id)
    
    if not user:
        # Check if user exists by email
        user = user_manager.get_user_by_email(email)
        
        if user:
            # Link GitHub account to existing user
            try:
                user = user_manager.link_github_account(user, github_id, github_username)
            except ValueError:
                return jsonify(error("409", "GitHub account already linked to another user")), 409
        else:
            # Create new user
            try:
                user = user_manager.create_user_from_github(
                    username=username,
                    email=email,
                    github_id=github_id,
                    github_username=github_username
                )
            except ValueError as e:
                if str(e) == "EMAIL_EXISTS":
                    return jsonify(error("409", "Email already exists")), 409
                raise
    
    # Generate JWT tokens
    tokens = make_tokens(identity=user.id, token_version=user.token_version)
    
    return jsonify({
        "access_token": tokens["access_token"],
        "expires_in": 60 * 30,
        "refresh_token": tokens["refresh_token"],
        "refresh_expires_in": 60 * 60 * 24 * 7,
        "token_type": "Bearer",
    }), 200
