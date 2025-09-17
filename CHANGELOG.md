# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-09-17
- Add role-based access with USER/ADMIN/SUPER_ADMIN.
- Seed default SUPER_ADMIN account via env (SUPER_ADMIN_EMAIL/USERNAME/PASSWORD).
- Admin APIs: list users, promote/demote ADMIN, reset user password.
- Password policy: min 8 chars with letters and digits.
- Force password-change flow after admin reset and for default SUPER_ADMIN.
- Add last login tracking and include in admin user list.
- Support login by email or username (username case-insensitive).
- Add version endpoint GET /api/v1/version and frontend display on login.
