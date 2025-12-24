# Admin Password Reset Process

This guide explains how admins/super-admins should securely reset a user's password and what the end user must do afterward.

## Roles and Permissions
- SUPER_ADMIN: Can promote/demote between USER and ADMIN; can reset any user’s password (including SUPER_ADMIN).
- ADMIN: Cannot change roles; can reset any user’s password (including SUPER_ADMIN).
- USER: No permission to perform this action.
- Note: Admins cannot reset their own password via admin APIs; they must use “Settings → Change Password”.

## UI Path (Frontend)
1. Sign in and open “User Management”.
2. Locate the target user and click “Reset Password”.
3. Confirm the action in the dialog.
4. The system generates a temporary password and displays it in a modal. Copy it and deliver it securely to the user.
   - Tip: The temporary password is only shown once. Keep it confidential.

## Backend Behavior
- The server generates a strong temporary password (>= 12 chars; includes upper/lower letters, digits and symbols).
- The user’s password is set to that value and `must_change_password` is set to true.
- The user’s `token_version` is incremented to invalidate existing sessions/refresh tokens (i.e., sign out everywhere).
- API response returns `{ message, temp_password }` for the admin to relay.

Endpoint: `POST /api/v1/admin/users/{user_id}/reset-password`
- Required role: ADMIN or higher
- Self reset: Returns 400 if `{user_id}` is the caller (use self change-password instead)

## End-User Flow & Suggested Message
- Example text to send to a user:
  - Your account password has been reset. Please sign in with the following temporary password: `<TEMP PASSWORD>`.
  - For your security, you will be redirected to change your password immediately after signing in (Settings → Change Password).
  - Password policy: At least 8 characters, must include letters and numbers. We recommend using mixed case and symbols for stronger security.

## First-Login Forced Password Change
- After signing in with the temporary password, the user is redirected to “Settings”, where a first-login guide appears and they must set a new password.
- Once the new password is set, the system signs out automatically and asks the user to sign in again with the new password.

## Security Recommendations
- Deliver the temporary password through a secure channel (e.g., controlled IM, phone verification, S/MIME email). Avoid public chats or searchable plain text.
- Remind the user to change their password promptly.
- If you suspect leakage of the temporary password, perform another reset immediately.
- Do not store temporary passwords in public locations or ticketing systems; avoid screenshots with plain text.

## FAQ
- Q: Can the user still use the old password?
  - A: No. The old password is replaced and sessions/refresh tokens are invalidated.
- Q: Why do I see 403 after signing in?
  - A: The user must change their password first. The app redirects them to “Settings” where they can complete the change.
- Q: Can an admin reset their own password here?
  - A: No. Admins must change their own passwords via “Settings → Change Password”.

---
If you need stricter controls (temporary password expiration, SMS/email templates, audit logs, approval flows, etc.), these can be added in future iterations.
