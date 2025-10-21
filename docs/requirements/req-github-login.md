# Feature: GitHub App Login

## Overview
Implement "Login with GitHub" feature to allow users to sign up and log in using their GitHub account via OAuth 2.0 Authorization Code flow.

## Requirements

### 1. Authentication Method
- Use GitHub App with OAuth 2.0 Authorization Code flow
- Implement standard OAuth flow: redirect → callback → token exchange

### 2. Frontend Changes
- Add "Login with GitHub" button on `/login` page
- Handle OAuth callback redirect
- Create `/login/complete-registration` page for email entry when GitHub email is private

### 3. Backend Changes

#### 3.1 Database Schema
Add to `users` table:
- `github_id` (Integer, Unique, Nullable) - GitHub user ID
- `github_username` (String, Nullable) - GitHub username

#### 3.2 API Endpoints
1. **GET /api/v1/auth/github/login**
   - Initiates OAuth flow
   - Redirects to GitHub authorization page

2. **GET /api/v1/auth/github/callback**
   - Handles GitHub OAuth callback
   - Exchanges authorization code for access token
   - Fetches user info from GitHub API
   - Creates or links user account
   - Returns JWT tokens

3. **POST /api/v1/auth/github/complete** (Optional for email privacy)
   - Accepts email from user when GitHub email is private
   - Completes registration
   - Returns JWT tokens

#### 3.3 Account Logic
- **Auto-registration**: Create new user if email doesn't exist
  - Username: GitHub username
  - Email: GitHub email or user-provided email
  - Password: Generate random hash (GitHub users won't use it)
  - Link GitHub ID and username
  
- **Auto-linking**: Link to existing user if email matches
  - Update `github_id` and `github_username` fields
  - User can then login via GitHub or traditional email/password

#### 3.4 Email Privacy Handling
- If GitHub user's email is private (null or empty):
  - Store GitHub ID and username in session/temporary storage
  - Redirect to `/login/complete-registration`
  - User enters email manually
  - Complete registration with provided email

### 4. Configuration
Add to `.env`:
```
GITHUB_CLIENT_ID=your_github_app_client_id
GITHUB_CLIENT_SECRET=your_github_app_client_secret
GITHUB_REDIRECT_URI=http://localhost:5000/api/v1/auth/github/callback
```

### 5. Error Handling
- **User cancels OAuth**: Redirect to login page with message "GitHub login cancelled"
- **API failure**: Show user-friendly error "GitHub login failed. Please try again."
- **Email already exists** (during manual entry): "Email already registered"
- **Invalid state parameter**: "Invalid OAuth state. Please try again."

### 6. Security Considerations
- Use state parameter to prevent CSRF attacks
- Validate state parameter in callback
- Store state in session with expiration
- Use HTTPS in production
- Don't expose client secret in frontend

## Technical Notes

### GitHub API Endpoints
- Authorization: `https://github.com/login/oauth/authorize`
- Token exchange: `https://github.com/login/oauth/access_token`
- User info: `https://api.github.com/user`

### OAuth Flow
1. Frontend: User clicks "Login with GitHub"
2. Backend: Generate state, redirect to GitHub authorize URL
3. GitHub: User authorizes app
4. GitHub: Redirects to callback URL with code
5. Backend: Exchange code for access token
6. Backend: Fetch user info from GitHub
7. Backend: Create/link user account
8. Backend: Generate JWT tokens
9. Frontend: Store tokens, redirect to dashboard

### Password Field for GitHub Users
- GitHub-authenticated users have `password_hash` set to a random value
- They cannot login with email/password method
- They can only login via GitHub OAuth
- Users can still set a password later if needed

## Acceptance Criteria
- [ ] User can click "Login with GitHub" button on login page
- [ ] OAuth flow completes successfully
- [ ] New user account is created with GitHub info
- [ ] Existing user account is linked with GitHub info
- [ ] User is redirected to dashboard after successful login
- [ ] Email privacy scenario works (manual email entry)
- [ ] Error messages are user-friendly
- [ ] All tests pass
