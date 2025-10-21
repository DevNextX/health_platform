# GitHub Login Feature - Setup and Usage Guide

This guide explains how to set up and use the GitHub OAuth login feature in the Health Platform.

## Overview

The GitHub login feature allows users to sign up and log in using their GitHub account. This is implemented using OAuth 2.0 Authorization Code flow with a GitHub App.

## Features

- ✅ One-click login with GitHub
- ✅ Automatic user registration for new users
- ✅ Automatic account linking for existing users
- ✅ Support for private GitHub email addresses
- ✅ Secure OAuth 2.0 implementation with CSRF protection
- ✅ Bilingual support (English/Chinese)

## Prerequisites

You need to create a GitHub App or OAuth App to use this feature:

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Fill in the application details:
   - **Application name**: Health Platform (or your preferred name)
   - **Homepage URL**: `http://localhost:3000` (or your production URL)
   - **Authorization callback URL**: `http://localhost:5000/api/v1/auth/github/callback`
4. Click "Register application"
5. Note down your **Client ID**
6. Generate a new **Client Secret** and save it securely

## Configuration

### Backend Configuration

Add the following environment variables to your `.env` file:

```bash
# GitHub OAuth Configuration
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here
GITHUB_REDIRECT_URI=http://localhost:5000/api/v1/auth/github/callback

# For production, use HTTPS:
# GITHUB_REDIRECT_URI=https://yourdomain.com/api/v1/auth/github/callback
```

### Frontend Configuration

The frontend automatically uses the backend API endpoints. No additional configuration is needed.

## Usage

### For End Users

1. **Login with GitHub**:
   - Navigate to the login page
   - Click the "Login with GitHub" button
   - Authorize the application on GitHub
   - You'll be automatically logged in

2. **Private Email Scenario**:
   - If your GitHub email is private, you'll be redirected to a registration completion page
   - Enter your email address
   - Click "Complete Registration"
   - You'll be logged in and your GitHub account will be linked

3. **Linking Existing Account**:
   - If you already have an account with the same email, your GitHub account will be automatically linked
   - You can then log in using either method (email/password or GitHub)

### API Endpoints

#### 1. Initiate GitHub Login
```
GET /api/v1/auth/github/login
```
Redirects user to GitHub authorization page.

#### 2. GitHub OAuth Callback
```
GET /api/v1/auth/github/callback?code=xxx&state=xxx
```
Handles the OAuth callback from GitHub. Automatically creates/links user account and redirects to frontend with tokens.

Query Parameters:
- `code` (required): Authorization code from GitHub
- `state` (required): CSRF protection state parameter
- `error` (optional): Error code if user cancelled

#### 3. Complete Registration (Private Email)
```
POST /api/v1/auth/github/complete
Content-Type: application/json

{
  "email": "user@example.com"
}
```
Completes registration when GitHub email is private.

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 1800,
  "refresh_expires_in": 604800,
  "token_type": "Bearer"
}
```

## Security

### Implemented Security Measures

1. **CSRF Protection**: Uses state parameter to prevent CSRF attacks
2. **Session Security**: OAuth state stored in secure Flask session
3. **HTTPS Ready**: Configuration supports HTTPS for production
4. **Secret Protection**: Client secret never exposed to frontend
5. **Token Security**: Uses JWT with refresh token rotation
6. **Email Validation**: Validates email format when manually entered

### Security Best Practices

1. **Never commit secrets**: Keep `.env` file out of version control
2. **Use HTTPS in production**: Always use HTTPS for OAuth callbacks
3. **Rotate secrets regularly**: Periodically regenerate your GitHub client secret
4. **Monitor access**: Review GitHub App access logs regularly
5. **Scope minimization**: Only request `user:email` scope (minimal required)

## Database Schema

### User Model Changes

Two new fields added to the `users` table:

```python
github_id = db.Column(db.Integer, unique=True, nullable=True)
github_username = db.Column(db.String(120), nullable=True)
```

- `github_id`: Unique identifier from GitHub (used for linking)
- `github_username`: GitHub username (for display/reference)

### Migration

If you have an existing database, the new columns will be automatically added when the application starts (for SQLite). For production databases (MySQL/PostgreSQL), you may need to run migrations manually:

```sql
ALTER TABLE users ADD COLUMN github_id INTEGER UNIQUE;
ALTER TABLE users ADD COLUMN github_username VARCHAR(120);
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run only GitHub OAuth tests
python -m pytest tests/test_github_oauth.py -v

# Run with coverage
python -m pytest tests/test_github_oauth.py --cov=src.service.github_auth_service
```

### Test Coverage

The test suite includes 12 comprehensive tests covering:
- ✅ Redirect to GitHub
- ✅ New user creation
- ✅ Existing user linking (by email)
- ✅ Existing GitHub user login
- ✅ Invalid state handling
- ✅ Missing parameters
- ✅ User cancellation
- ✅ Private email scenario
- ✅ Email completion flow
- ✅ Error scenarios

## Troubleshooting

### Common Issues

1. **"Invalid OAuth state" error**
   - Cause: Session expired or CSRF attack attempt
   - Solution: Clear browser cookies and try again

2. **"GitHub login failed" error**
   - Cause: Invalid client ID/secret or GitHub API error
   - Solution: Verify your `.env` configuration

3. **"Email already exists" error**
   - Cause: Email is registered with a different account
   - Solution: User should login with email/password first, or use a different email

4. **Redirect URI mismatch**
   - Cause: Callback URL in GitHub App doesn't match `GITHUB_REDIRECT_URI`
   - Solution: Update GitHub App settings or `.env` file

### Debug Mode

Enable Flask debug mode for detailed error messages:

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
```

### Logs

Check application logs for OAuth flow details:
```bash
tail -f logs/app.log
```

## Production Deployment

### Checklist

- [ ] Create production GitHub OAuth App
- [ ] Set `GITHUB_REDIRECT_URI` to production HTTPS URL
- [ ] Update GitHub App callback URL in GitHub settings
- [ ] Use strong `SECRET_KEY` for Flask sessions
- [ ] Enable HTTPS/TLS on your server
- [ ] Set appropriate CORS_ORIGINS
- [ ] Test OAuth flow in production environment
- [ ] Monitor error logs
- [ ] Set up rate limiting (already configured)

### Example Production Configuration

```bash
# .env (production)
GITHUB_CLIENT_ID=prod_client_id
GITHUB_CLIENT_SECRET=prod_client_secret_keep_secure
GITHUB_REDIRECT_URI=https://healthplatform.example.com/api/v1/auth/github/callback
SECRET_KEY=your-strong-random-secret-key-here
JWT_SECRET=your-jwt-secret-here
CORS_ORIGINS=https://healthplatform.example.com
```

## Architecture

### OAuth Flow Diagram

```
User → Frontend (Login) → Backend (GitHub Login Endpoint)
                              ↓
                         GitHub Authorization
                              ↓
        Frontend ← Backend (Callback Handler) ← GitHub
            ↓
      Dashboard (Logged In)
```

### Components

1. **Frontend**:
   - `Login.js`: Login page with GitHub button
   - `LoginCallback.js`: Handles OAuth redirect with tokens
   - `CompleteRegistration.js`: Email entry for private email scenario

2. **Backend**:
   - `github_auth_service.py`: OAuth endpoints
   - `github_oauth_manager.py`: OAuth flow logic
   - `user_manager.py`: User creation and linking

3. **Database**:
   - `models.py`: User model with GitHub fields

## Support

For issues or questions:
1. Check this guide and troubleshooting section
2. Review test cases in `tests/test_github_oauth.py`
3. Check application logs
4. Open an issue on GitHub repository

## References

- [GitHub OAuth Documentation](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps)
- [OAuth 2.0 RFC](https://datatracker.ietf.org/doc/html/rfc6749)
- [Flask Session Documentation](https://flask.palletsprojects.com/en/2.3.x/api/#sessions)
