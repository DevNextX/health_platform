# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-17

### Added

#### Admin and User Management System
- **Multi-level role system**: Implemented USER, ADMIN, and SUPER_ADMIN roles with strict permissions
- **Super admin initialization**: Automatic creation of super admin account on first startup
- **Admin user management**: Admins can view and manage users (role restrictions apply)
- **Role management**: Super admins can promote/demote users between USER and ADMIN roles
- **Password reset functionality**: Admins can reset user passwords with secure temporary passwords
- **User list API**: Role-filtered user listing with pagination support

#### Enhanced Authentication & Security  
- **Case-insensitive login**: Users can login with username or email (case insensitive)
- **Password strength requirements**: Enforced 8+ character passwords with letters and numbers
- **Forced password changes**: Users must change passwords after admin resets
- **Self-service password change**: Users can change their own passwords securely
- **Token invalidation**: Password changes invalidate all existing JWT tokens
- **Protected super admin**: Super admin accounts cannot be deleted or demoted

#### Version Management
- **System versioning**: Added version configuration and API endpoint
- **Version API**: `GET /api/v1/version` returns current system version
- **Changelog documentation**: Comprehensive change tracking system

#### Database & Infrastructure
- **Database migrations**: Added migration system for schema updates  
- **Role fields**: Added `role` and `must_change_password` columns to users table
- **CLI commands**: Added admin migration and super admin initialization commands

### Security

#### Access Control
- **Endpoint protection**: Admin APIs require appropriate role permissions
- **JWT validation**: Enhanced token validation with version checking
- **Permission boundaries**: Strict enforcement of role-based access control
- **401/403 distinction**: Clear separation of authentication vs authorization errors

#### Password Security  
- **Secure password generation**: 8-character random passwords for resets
- **Password hashing**: All passwords properly hashed using Werkzeug security
- **Session invalidation**: Password changes force re-authentication

### API Changes

#### New Endpoints
- `GET /api/v1/admin/users` - List users (Admin+)
- `GET /api/v1/admin/users/{id}` - Get user details (Admin+)  
- `PUT /api/v1/admin/users/{id}/role` - Change user role (Super Admin only)
- `POST /api/v1/admin/users/{id}/password/reset` - Reset user password (Admin+)
- `GET /api/v1/admin/stats` - Get admin statistics (Admin+)
- `POST /api/v1/auth/change-password` - Change own password
- `POST /api/v1/auth/force-change-password` - Force password change flow
- `GET /api/v1/version` - Get system version

#### Modified Endpoints  
- `POST /api/v1/auth/login` - Now supports username/email login, returns user info
- `POST /api/v1/auth/register` - Now validates password strength

### Configuration

#### Environment Variables
- `SUPER_ADMIN_USERNAME` - Super admin username (default: admin)
- `SUPER_ADMIN_EMAIL` - Super admin email (default: admin@healthplatform.local) 
- `SUPER_ADMIN_PASSWORD` - Super admin password (default: Admin123)

#### Version Configuration
- Added `VERSION = "1.0.0"` to application config

### CLI Commands

#### New Commands
- `flask migrate-admin` - Apply admin fields migration
- `flask init-super-admin` - Initialize super admin user

### Development

#### Code Structure
- **Authorization decorators**: Reusable role-checking decorators
- **Enhanced user manager**: Extended with role and password management
- **Admin utilities**: Role validation and permission checking utilities
- **Migration system**: Database schema migration framework

### Breaking Changes

#### Database Schema
- Added `role` column to users table (default: USER)
- Added `must_change_password` column to users table (default: false)

#### API Behavior  
- Login endpoint now returns additional user information
- Registration now validates password strength
- All password changes now invalidate existing tokens

---

**Migration Notes:**
- Existing users will be assigned USER role by default
- Super admin account will be created on first startup  
- Run `flask migrate-admin` to apply database changes
- Update frontend to handle new authentication flows