# WeChat Login Feature - Deployment Guide

## Overview
This document provides guidance for deploying the WeChat login feature in production.

## Database Migration

Before deploying, you need to update the database schema:

### SQLite
```sql
ALTER TABLE users ADD COLUMN wechat_openid VARCHAR(128) UNIQUE;
-- SQLite doesn't support modifying column constraints directly
-- Create a new table and copy data if needed, or use SQLAlchemy's create_all()
```

### MySQL/PostgreSQL
```sql
ALTER TABLE users ADD COLUMN wechat_openid VARCHAR(128) UNIQUE;
ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(256) NULL;
```

**Note**: The application will automatically create tables if they don't exist using SQLAlchemy's `db.create_all()`.

## Environment Variables

Add the following environment variables to your `.env` file or deployment configuration:

```bash
# WeChat Open Platform Configuration
WECHAT_APP_ID=your_wechat_app_id_here
WECHAT_APP_SECRET=your_wechat_app_secret_here
WECHAT_REDIRECT_URI=https://yourdomain.com/wechat/callback
```

### Obtaining WeChat Credentials

1. Register at [WeChat Open Platform](https://open.weixin.qq.com/)
2. Complete developer verification (requires business license)
3. Create a "Website Application"
4. Configure the authorization callback domain
5. Obtain AppID and AppSecret from the application settings

## Production Considerations

### 1. State Storage (Important!)

The current MVP implementation uses in-memory storage for authentication states, which:
- Won't work across multiple server instances
- Will lose state on server restart
- Is not suitable for production

**Recommended Solution**: Implement Redis-backed state storage

Example implementation:
```python
import redis
import json
from datetime import timedelta

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0))
)

def store_wechat_state(state, data, expire=600):
    """Store WeChat state in Redis with expiration"""
    redis_client.setex(
        f"wechat:state:{state}",
        timedelta(seconds=expire),
        json.dumps(data)
    )

def get_wechat_state(state):
    """Retrieve WeChat state from Redis"""
    data = redis_client.get(f"wechat:state:{state}")
    if data:
        return json.loads(data)
    return None

def delete_wechat_state(state):
    """Delete WeChat state from Redis"""
    redis_client.delete(f"wechat:state:{state}")
```

### 2. HTTPS Requirement

WeChat Open Platform requires HTTPS for the redirect URI. Ensure your production deployment uses:
- Valid SSL/TLS certificate
- HTTPS for all WeChat-related endpoints

### 3. Frontend Build

Build the frontend for production:
```bash
cd frontend
npm run build
```

The build output will be in `frontend/build/`. Configure your web server to serve these static files.

### 4. CORS Configuration

Ensure CORS is properly configured for your production domain:
```python
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Testing the Integration

### 1. Backend Health Check
```bash
curl https://yourdomain.com/api/healthz
```

### 2. WeChat Login Endpoint
```bash
curl https://yourdomain.com/api/v1/auth/wechat/login
```
Should return a QR code URL and state.

### 3. Frontend Access
Navigate to `https://yourdomain.com/login` and verify the "Login with WeChat" button appears.

## Troubleshooting

### "WeChat configuration missing" error
- Verify `WECHAT_APP_ID`, `WECHAT_APP_SECRET`, and `WECHAT_REDIRECT_URI` are set
- Check environment variables are loaded correctly

### "Invalid or expired state" error
- If using multiple servers, implement Redis-backed state storage
- Check state expiration time (default: 10 minutes)

### WeChat callback not working
- Verify redirect URI matches exactly in WeChat Open Platform settings
- Ensure domain is authorized in WeChat Open Platform
- Check HTTPS is enabled

### Users can't login with email after WeChat registration
- This is expected behavior for WeChat-only users (no password set)
- Users must set a password during email binding to enable email login

## Security Checklist

- [ ] HTTPS enabled for production
- [ ] Redis or database-backed state storage implemented
- [ ] Environment variables properly secured
- [ ] WeChat AppSecret never exposed to frontend
- [ ] Rate limiting configured appropriately
- [ ] Error messages don't expose sensitive information
- [ ] CORS origins restricted to trusted domains

## Monitoring

Monitor the following metrics:
- WeChat login attempts vs successes
- State expiration rate
- Email binding completion rate
- Login method distribution (email vs WeChat)

## Support

For issues related to:
- **Application**: Check application logs for detailed error messages
- **WeChat API**: Refer to [WeChat Open Platform Documentation](https://developers.weixin.qq.com/doc/oplatform/en/Website_App/WeChat_Login/Wechat_Login.html)
- **Database**: Ensure migrations are applied correctly

## Rollback Plan

If issues occur:
1. Remove "Login with WeChat" button from frontend
2. Set `WECHAT_APP_ID=""` to disable WeChat endpoints
3. Existing users can still login with email/password
4. No data loss as WeChat OpenID is stored separately
