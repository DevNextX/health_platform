# WeChat QR Code Login Integration

## Overview

This document describes the WeChat QR Code login feature implemented in the Health Platform. This feature allows users to login using their WeChat account by scanning a QR code.

## Features

### 1. WeChat Login (New Users)
- Users can click the "WeChat Login" button on the login page
- A QR code is displayed in a modal dialog
- Users scan the QR code with their WeChat app
- Upon successful authentication, a new account is automatically created
- Users are logged in and redirected to the dashboard

### 2. WeChat Login (Existing WeChat Users)
- Previously registered WeChat users can login directly by scanning the QR code
- The system identifies users by their WeChat `unionid`
- Users are logged in and redirected to the dashboard

### 3. Binding WeChat to Existing Account
- Users with existing email/password accounts can bind their WeChat account
- Navigate to Profile page → WeChat Account section
- Click "Bind WeChat" button
- Scan the displayed QR code with WeChat
- WeChat account is linked to the existing user account

## Configuration

### Backend Configuration

Add the following environment variables to your `.env` file:

```bash
# WeChat OAuth Configuration
WECHAT_APP_ID=your_wechat_app_id
WECHAT_APP_SECRET=your_wechat_app_secret
WECHAT_REDIRECT_URI=http://localhost:3000/auth/wechat/callback
```

### Getting WeChat Credentials

1. Register for WeChat Open Platform at https://open.weixin.qq.com
2. Create a "Website Application" (网站应用)
3. Complete the developer verification process
4. Obtain your `AppID` and `AppSecret`
5. Configure the authorized redirect URI

## API Endpoints

### Get QR Code Parameters
```
GET /api/v1/auth/wechat/qr
```

Returns parameters needed to generate the WeChat login QR code.

**Response:**
```json
{
  "qr_url": "https://open.weixin.qq.com/connect/qrconnect?...",
  "appid": "your_app_id",
  "state": "STATE"
}
```

### WeChat Callback
```
POST /api/v1/auth/wechat/callback
```

Exchange WeChat authorization code for access tokens and user information.

**Request:**
```json
{
  "code": "authorization_code_from_wechat"
}
```

**Response:**
```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token",
  "expires_in": 1800,
  "refresh_expires_in": 604800,
  "token_type": "Bearer",
  "user": {
    "id": 1,
    "username": "WeChat User",
    "email": null,
    "is_wechat_user": true,
    "avatar_url": "http://..."
  }
}
```

### Bind WeChat Account
```
POST /api/v1/auth/wechat/bind
Authorization: Bearer <access_token>
```

Bind a WeChat account to the currently logged-in user.

**Request:**
```json
{
  "code": "authorization_code_from_wechat"
}
```

**Response:**
```json
{
  "message": "WeChat account bound successfully",
  "user": {
    "id": 1,
    "username": "User Name",
    "email": "user@example.com",
    "wechat_bound": true,
    "avatar_url": "http://..."
  }
}
```

## Database Schema Changes

### User Table Additions

Three new columns were added to the `users` table:

- `wechat_unionid` (VARCHAR(128), UNIQUE, NULLABLE, INDEXED): WeChat union ID for identifying users
- `avatar_url` (VARCHAR(512), NULLABLE): URL to user's WeChat avatar
- `is_wechat_user` (BOOLEAN, DEFAULT FALSE): Flag indicating if user registered via WeChat

The `password_hash` column is now nullable to support WeChat-only users who don't have a password.

## Security Considerations

### 1. OAuth 2.0 Compliance
- Follows WeChat OAuth 2.0 protocol
- Authorization code is exchanged for access token server-side
- Access tokens are never exposed to the client

### 2. CSRF Protection
- State parameter should be implemented with random values
- Verify state parameter matches on callback

### 3. Token Security
- WeChat access tokens are used only for initial authentication
- System uses its own JWT tokens for session management
- Refresh token rotation is implemented

### 4. Data Privacy
- Only essential WeChat user data is stored (unionid, nickname, avatar)
- WeChat credentials (AppID, AppSecret) are stored in environment variables
- Password field is nullable for WeChat-only users

## Testing

### Unit Tests

Run the WeChat-specific test suite:
```bash
pytest tests/test_wechat.py -v
```

All 11 tests cover:
- QR code generation
- WeChat callback handling (new and existing users)
- Account binding
- Error handling
- Manager layer functionality

### Manual Testing

Due to WeChat OAuth requiring actual WeChat credentials and verification:

1. Configure valid WeChat App credentials
2. Access the login page
3. Click "WeChat Login" button
4. Scan QR code with WeChat mobile app
5. Authorize the application
6. Verify successful login
7. Test binding flow from Profile page

## Frontend Components

### WeChatQRModal
Reusable modal component for displaying WeChat QR codes.

**Props:**
- `visible` (boolean): Controls modal visibility
- `onClose` (function): Called when modal is closed
- `onSuccess` (function): Called after successful WeChat authentication

### Login Page Updates
- Added WeChat login button with WeChat green color (#07C160)
- Integrated WeChat callback handling
- Displays QR code modal on button click

### Profile Page Updates
- Added WeChat Account section showing binding status
- Bind WeChat button for unbound accounts
- Visual indicator for bound accounts

## Internationalization

All WeChat-related text supports both English and Chinese:
- Login page labels
- QR code modal text
- Profile page WeChat section
- Success/error messages

Translation keys are located in:
- `frontend/src/i18n/locales/en/translation.json`
- `frontend/src/i18n/locales/zh/translation.json`

## Limitations

### Current Scope
- PC web application only
- WeChat Open Platform integration (not WeChat Official Account)
- Auto-registration for new WeChat users
- Single WeChat account per user account

### Out of Scope
- Mobile app WeChat integration
- WeChat Mini Program integration
- WeChat Pay integration
- Account unbinding functionality
- Account merging for multiple existing accounts

## Troubleshooting

### QR Code Not Loading
- Verify WeChat credentials are configured
- Check backend server is running
- Verify network connectivity to WeChat API

### WeChat Login Fails
- Ensure redirect URI matches WeChat Open Platform configuration
- Check WeChat App is approved and active
- Verify user has authorized the application

### Binding Fails with "Already Bound"
- The WeChat account is already linked to another user
- User must unbind from the other account first (not implemented in current version)

## Future Enhancements

Potential improvements for future iterations:

1. **Account Unbinding**: Allow users to disconnect their WeChat account
2. **QR Code Polling**: Automatically check for scan completion without page refresh
3. **State Parameter Enhancement**: Use cryptographically secure random state values
4. **Avatar Sync**: Automatically update user avatar from WeChat
5. **Mobile Support**: Add WeChat OAuth for mobile web browsers
6. **Account Merging**: Handle merging of data when binding accounts

## Support

For issues or questions:
- Review this documentation
- Check application logs for errors
- Verify WeChat Open Platform configuration
- Consult WeChat Open Platform documentation: https://developers.weixin.qq.com/doc/oplatform/en/Website_App/WeChat_Login/Wechat_Login.html

Generated by Copilot.
