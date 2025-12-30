# Health Platform API Design

## Overview

This document describes the REST API endpoints for the Health Platform, including the batch import functionality.

## Base URL

```
Development: http://localhost:5000/api/v1
Production: https://your-domain.com/api/v1
```

## Authentication

All endpoints require JWT authentication except for registration and login.

**Header:**
```
Authorization: Bearer <access_token>
```

---

## Health Record Endpoints

### 1. Create Health Record

**POST** `/health`

Create a single health record.

**Request Body:**
```json
{
  "systolic": 120,
  "diastolic": 80,
  "heart_rate": 72,
  "timestamp": "2025-12-19T08:30:00Z",
  "tags": ["晨起", "空腹"],
  "note": "早晨测量",
  "subject_member_id": 1
}
```

**Response:** `201 Created`
```json
{
  "id": 123,
  "systolic": 120,
  "diastolic": 80,
  "heart_rate": 72,
  "timestamp": "2025-12-19T08:30:00Z",
  "tags": ["晨起", "空腹"],
  "note": "早晨测量",
  "created_at": "2025-12-19T08:35:00Z",
  "subject_member_id": 1
}
```

### 2. List Health Records

**GET** `/health`

List health records with pagination and filters.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `size` (int): Records per page (default: 10, max: 100)
- `tags` (string): Comma-separated tag list
- `date_from` (ISO8601): Start date filter
- `date_to` (ISO8601): End date filter
- `subject_member_id` (int): Filter by member

**Response:** `200 OK`
```json
{
  "records": [...],
  "pagination": {
    "total": 100,
    "page": 1,
    "size": 10,
    "pages": 10
  }
}
```

### 3. Get Single Health Record

**GET** `/health/{record_id}`

Get a specific health record.

**Response:** `200 OK`

### 4. Update Health Record

**PUT** `/health/{record_id}`

Update a health record.

**Request Body:** Same as Create (all fields optional)

**Response:** `200 OK`

### 5. Delete Health Record

**DELETE** `/health/{record_id}`

Delete a health record.

**Response:** `200 OK`
```json
{
  "message": "Record deleted successfully."
}
```

### 6. Export Health Records (CSV)

**GET** `/health/export`

Export health records as CSV file.

**Query Parameters:** Same as List endpoint

**Response:** `200 OK`
- Content-Type: `text/csv; charset=utf-8`
- Content-Disposition: Includes filename with UTF-8 support

---

## Batch Import Endpoints

### 7. Batch Import Health Records

**POST** `/health/batch-import`

Import multiple health records from Excel or CSV file.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field

**File Requirements:**
- Format: `.xlsx` (Excel) or `.csv` (UTF-8)
- Max size: 5 MB
- Max records: 1000 per import

**CSV/Excel Columns:**

| Column Name (中文) | Column Name (EN) | Required | Type | Range/Format |
|-------------------|------------------|----------|------|--------------|
| 成员名称 | Member Name | ✅ | String | Member full name or Self/自己/本人 |
| 测量时间 | Timestamp | ✅ | DateTime | ISO8601 or common formats |
| 收缩压 | Systolic | ✅ | Integer | 30-250 mmHg |
| 舒张压 | Diastolic | ✅ | Integer | 30-250 mmHg |
| 心率 | Heart Rate | ⭕ | Integer | 30-150 bpm |
| 标签 | Tags | ⭕ | String | Semicolon or comma separated |
| 备注 | Note | ⭕ | String | Max 500 characters |

**Example CSV:**
```csv
成员名称,测量时间,收缩压,舒张压,心率,标签,备注
Self,2025-12-19 08:30:00,120,80,72,晨起;空腹,早晨测量
张三,2025-12-18 20:00:00,135,85,78,晚餐后,感觉有点头晕
```

**Response:** `200 OK`
```json
{
  "success": true,
  "summary": {
    "total_rows": 10,
    "success_count": 8,
    "error_count": 2
  },
  "errors": [
    {
      "row": 3,
      "data": {
        "member_name": "张三",
        "timestamp": "2025-12-19 08:30:00",
        "systolic": 25,
        "diastolic": 80
      },
      "errors": ["Systolic must be between 30-250 mmHg"]
    }
  ]
}
```

**Error Responses:**
- `400 Bad Request`: Invalid file format, size exceeded, or validation errors
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Member doesn't belong to user's household

### 8. Download Import Template

**GET** `/health/batch-import/template`

Download a template file for batch import.

**Query Parameters:**
- `format` (string): Template format - `excel` or `csv` (default: `excel`)

**Response:** `200 OK`
- Content-Type: 
  - Excel: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
  - CSV: `text/csv; charset=utf-8`
- Content-Disposition: Includes filename

**Example:**
```
GET /health/batch-import/template?format=excel
GET /health/batch-import/template?format=csv
```

### 9. Download Error Log

**POST** `/health/batch-import/errors`

Download error log from a batch import operation.

**Request Body:**
```json
{
  "errors": [
    {
      "row": 2,
      "data": {
        "member_name": "Test",
        "timestamp": "2025-12-19 08:30:00",
        "systolic": 25,
        "diastolic": 80
      },
      "errors": ["Systolic must be between 30-250 mmHg"]
    }
  ]
}
```

**Response:** `200 OK`
- Content-Type: `text/csv; charset=utf-8`
- Content-Disposition: Filename with timestamp

---

## Data Validation Rules

### Blood Pressure
- **Range**: 30-250 mmHg for both systolic and diastolic
- **Relationship**: Systolic must be greater than diastolic

### Heart Rate
- **Range**: 30-150 bpm
- **Optional**: Can be omitted or empty

### Timestamp
- **Default Timezone**: Beijing time (UTC+8) for naive timestamps
- **Storage**: All timestamps stored as UTC in database
- **Supported Formats**:
  - `2025-12-19 08:30:00`
  - `2025-12-19T08:30:00`
  - `2025-12-19T08:30:00+08:00`
  - `2025-12-19T08:30:00Z`

### Member Matching
- **Case Insensitive**: Member name matching is not case-sensitive
- **Trimming**: Leading and trailing spaces are automatically removed
- **Special Values**: `Self`, `自己`, `本人` all map to the user's Self member
- **Validation**: Member must belong to the user's household

### Tags
- **Format**: Semicolon (`;`) or comma (`,`) separated values
- **Storage**: Stored as JSON array
- **Display**: Tags are displayed with i18n labels

### Notes
- **Max Length**: 500 characters
- **Optional**: Can be empty

---

## Error Handling

### Standard Error Response

```json
{
  "code": "400",
  "message": "Validation error",
  "details": {
    "field_name": ["error message"]
  }
}
```

### Common Error Codes

- `400`: Bad Request - Invalid input data
- `401`: Unauthorized - Missing or invalid token
- `403`: Forbidden - Access denied
- `404`: Not Found - Resource doesn't exist
- `500`: Internal Server Error - Server-side error

### Batch Import Error Types

1. **File Validation Errors**
   - File size exceeds 5MB
   - Unsupported file format
   - Missing required columns

2. **Data Validation Errors** (Per Row)
   - Required fields missing
   - Values out of range
   - Invalid data format
   - Member not found
   - Systolic ≤ Diastolic

3. **Processing Errors**
   - Maximum 1000 records exceeded
   - File parsing failure

---

## Rate Limiting

- **Import Limit**: 1000 records per batch
- **File Size**: 5 MB maximum
- **Concurrent Imports**: Not recommended (sequential processing)

---

## Performance Considerations

### Batch Import
- **Processing Time**: < 10 seconds for 1000 records
- **Transaction**: All successful records committed in single transaction
- **Error Handling**: Failed rows are skipped; successful rows are imported

### Optimization
- Uses SQLAlchemy `bulk_save_objects()` for efficient batch insertion
- Single database transaction per import
- Minimal memory footprint through streaming where possible

---

## Security

### Authentication
- JWT tokens required for all endpoints
- Tokens expire after configured duration
- Refresh tokens supported for session extension

### Authorization
- Users can only access their own health records
- Member validation ensures users can only import data for members in their household
- Admin endpoints have additional role checks

### Data Privacy
- All data is user-scoped
- No cross-user data access
- Secure file handling (no persistent storage of uploaded files)

---

## Testing

### Unit Tests
- 22 batch import tests covering all scenarios
- 15 health record endpoint tests
- All tests pass with 100% success rate

### Manual Testing
- Template download (Excel & CSV)
- File upload and validation
- Import with various file formats
- Error handling and error log download

### Test Data
Sample files available in `/tmp/` directory:
- `health_records_sample_10.csv`
- `health_records_sample_50.xlsx`
- `health_records_with_errors.csv`

---

## Changelog

### v1.6 - Batch Import Feature
- Added batch import endpoint
- Added template download endpoint
- Added error log export endpoint
- Support for Excel and CSV formats
- Comprehensive validation and error handling
- Chinese and English column headers support

---

## Additional Resources

- [Batch Import User Guide](./BATCH_IMPORT.md)
- [Quick Start Guide](./BATCH_IMPORT_QUICKSTART.md)
- [Implementation Summary](./BATCH_IMPORT_SUMMARY.md)
