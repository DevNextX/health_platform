# API Design for Health Platform

## Authentication
- **Method**: JWT (JSON Web Token)
- **Header**: `Authorization: Bearer <token>`
- **Endpoints**:
  - `/api/auth/login` (POST): User login, returns a JWT token.
  - `/api/auth/register` (POST): User registration.
  - `/api/auth/refresh` (POST): Refresh tokens (requires refresh token).
  - `/api/auth/logout` (POST): Logout current session (requires refresh token).
  - `/api/auth/logout-all` (POST): Invalidate all sessions (requires access token).

---

## User Module
### 1. Register User
- **Endpoint**: `/api/user`
- **Method**: POST
- **Request DTO**:
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string",
    "age": "integer",
    "gender": "string",
    "weight": "float"
  }
  ```
- **Response DTO**:
  ```json
  {
    "id": "string",
    "username": "string",
    "email": "string",
    "created_at": "datetime"
  }
  ```

### 2. Login User
- **Endpoint**: `/api/auth/login`
- **Method**: POST
- **Request DTO**:
  ```json
  {
    "email": "string",
    "password": "string"
  }
  ```
- **Response DTO**:
  ```json
  {
    "token": "string",
    "expires_in": "integer"
  }
  ```

### 3. Get User Info
- **Endpoint**: `/api/user/{id}`
- **Method**: GET
- **Response DTO**:
  ```json
  {
    "id": "string",
    "username": "string",
    "email": "string",
    "age": "integer",
    "gender": "string",
    "weight": "float"
  }
  ```

### 4. Update User Info
- **Endpoint**: `/api/user/{id}`
- **Method**: PUT
- **Request DTO**:
  ```json
  {
    "username": "string",
    "age": "integer",
    "gender": "string",
    "weight": "float"
  }
  ```
- **Response DTO**:
  ```json
  {
    "id": "string",
    "username": "string",
    "email": "string",
    "updated_at": "datetime"
  }
  ```

---

## Health Data Module
### 1. Add Health Record
- **Endpoint**: `/api/health`
- **Method**: POST
- **Request DTO**:
  ```json
  {
    "systolic": "integer",
    "diastolic": "integer",
    "heart_rate": "integer",
    "timestamp": "datetime",
    "tags": ["string"],
    "note": "string"
  }
  ```
- **Response DTO**:
  ```json
  {
    "id": "string",
    "user_id": "string",
    "systolic": "integer",
    "diastolic": "integer",
    "heart_rate": "integer",
    "timestamp": "datetime",
    "tags": ["string"],
    "note": "string"
  }
  ```

### 2. Get Health Records
- **Endpoint**: `/api/health`
- **Method**: GET
- **Query Parameters**:
  - `user_id`: Filter by user.
  - `page`: Page number (default: 1).
  - `size`: Page size (default: 20).
  - `tags`: Filter by tags.
  - `date_from`: Start date.
  - `date_to`: End date.
- **Response DTO**:
  ```json
  {
    "data": [
      {
        "id": "string",
        "systolic": "integer",
        "diastolic": "integer",
        "heart_rate": "integer",
        "timestamp": "datetime",
        "tags": ["string"],
        "note": "string"
      }
    ],
    "pagination": {
      "page": "integer",
      "size": "integer",
      "total": "integer"
    }
  }
  ```

### 3. Update Health Record
- **Endpoint**: `/api/health/{id}`
- **Method**: PUT
- **Request DTO**:
  ```json
  {
    "systolic": "integer",
    "diastolic": "integer",
    "heart_rate": "integer",
    "tags": ["string"],
    "note": "string"
  }
  ```
- **Response DTO**:
  ```json
  {
    "id": "string",
    "systolic": "integer",
    "diastolic": "integer",
    "heart_rate": "integer",
    "tags": ["string"],
    "note": "string",
    "updated_at": "datetime"
  }
  ```

### 4. Delete Health Record
- **Endpoint**: `/api/health/{id}`
- **Method**: DELETE
- **Response DTO**:
  ```json
  {
    "message": "Record deleted successfully."
  }
  ```
