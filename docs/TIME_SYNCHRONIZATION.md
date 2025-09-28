# Time Synchronization

This document describes the time synchronization functionality implemented to resolve frontend-backend time discrepancy issues.

## Problem

JWT tokens have expiration times based on server time. When the client's system time is significantly different from the server's time, it can cause authentication issues:

- Token refresh failures (401 Unauthorized errors)
- Premature token expiration from the client's perspective
- Authentication loops requiring server/client restarts

## Solution

### Backend Changes

1. **Timezone-aware UTC timestamps**: Updated all datetime operations to use `datetime.now(UTC)` instead of the deprecated `datetime.utcnow()`
2. **Server time endpoint**: Added `/api/v1/auth/server-time` endpoint that returns:
   ```json
   {
     "server_time": "2024-01-01T12:00:00Z",
     "timestamp": 1704110400000
   }
   ```

### Frontend Changes

1. **Time synchronization utilities** (`src/utils/timeSync.js`):
   - `checkTimeDiscrepancy()`: Compares client time with server time
   - `formatTimeDiscrepancy()`: Formats time difference for user display
   - `shouldRecheckTimeSync()`: Determines when to recheck (every 30 minutes)

2. **Warning component** (`src/components/TimeDiscrepancyWarning.js`):
   - Displays warning when time discrepancy > 5 minutes
   - Shows both server and client times
   - Provides recheck and dismiss options

3. **Integration**: Added to main Layout component to appear on all authenticated pages

## Usage

### Automatic Detection

The frontend automatically checks for time discrepancies when:
- The application loads
- Every 30 minutes during active use
- When manually requested by the user

### Manual Testing

You can test the server time endpoint:

```bash
curl http://localhost:5000/api/v1/auth/server-time
```

### Configuration

Time discrepancy threshold can be adjusted in `frontend/src/utils/timeSync.js`:

```javascript
const TIME_DISCREPANCY_THRESHOLD = 5 * 60 * 1000; // 5 minutes in milliseconds
```

## Implementation Details

### Backend (`src/service/auth_service.py`)

```python
@auth_bp.route("/server-time", methods=["GET"])
def get_server_time():
    """Get current server time in UTC for client synchronization"""
    current_time = datetime.now(UTC)
    return jsonify({
        "server_time": current_time.isoformat().replace("+00:00", "Z"),
        "timestamp": int(current_time.timestamp() * 1000)
    }), 200
```

### Frontend Time Check

The frontend uses the fetch API to avoid authentication interceptors that could interfere with time checking:

```javascript
const response = await fetch('/api/v1/auth/server-time');
const data = await response.json();
const serverTime = new Date(data.server_time);
```

### Network Latency Compensation

The client takes the average of timestamps before and after the network request to account for network latency:

```javascript
const clientTime = new Date((timeBeforeRequest + timeAfterRequest) / 2);
```

## Testing

### Unit Tests

- `tests/test_time_sync.py`: Backend endpoint tests
- `tests/test_auth.py`: Updated auth tests including server-time endpoint

### Manual Testing

1. Change your system time by more than 5 minutes
2. Load the application
3. You should see a warning banner with time discrepancy information

## Benefits

1. **Proactive detection**: Users are warned about time issues before they cause authentication problems
2. **User education**: Clear explanation of the issue and suggested resolution
3. **Improved reliability**: Reduces authentication failures due to time discrepancies
4. **Debugging aid**: Developers can quickly identify time-related issues

## Future Enhancements

1. **Automatic time adjustment**: Could potentially adjust client-side token validation based on detected time offset
2. **Server monitoring**: Log time discrepancies for monitoring system clock drift
3. **Configurable thresholds**: Allow different warning thresholds for different environments