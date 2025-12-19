# Three-Tier Threshold Configuration Implementation

## Summary
Successfully implemented a three-tier threshold configuration system for blood pressure metrics, allowing Super Admins to configure:
1. **Healthy Lower** (min)
2. **Healthy Upper** (max)
3. **Borderline Upper** (borderline_max)

## Status Model
- **Healthy**: All values within `[min, max]`
- **Borderline**: BP values in `(max, borderline_max]` (none out of range)
- **Out of Range**: Any value outside all defined ranges

## Changes Made

### 1. Frontend Updates ([SuperAdminSettings.js](frontend/src/pages/SuperAdminSettings.js))

#### Added Form Fields
```javascript
// New default values
systolicBorderline: 140,
diastolicBorderline: 90,
```

#### Updated Form Layout
- Changed from 2-column (Lower/Upper) to 3-column layout (Lower/Upper/Borderline)
- Added `systolicBorderline` and `diastolicBorderline` input fields
- Heart rate remains 2-column (no borderline needed)

#### New Validation Function
```javascript
createBorderlineRule(upperKey, type) {
  // Ensures borderline > upper
  // Validates range 30-250 for BP
}
```

#### Updated Payload Builder
Changed from `{lower, upper}` to `{min, max, borderline_max}`:
```javascript
systolic: {
  min: values.systolicLow,
  max: values.systolicHigh,
  borderline_max: values.systolicBorderline
}
```

#### Updated Data Parser
`deriveFormValues()` now extracts `borderline_max` from backend payload.

### 2. Backend Updates ([threshold_manager.py](src/manager/threshold_manager.py))

#### Enhanced Validation
- Validates `min < max < borderline_max` for systolic/diastolic
- Validates `min < max` for heart_rate (no borderline)
- Enforces borderline_max presence for BP metrics
- Checks borderline_max within hard limits (30-250)

#### Updated Status Computation
`_compute_status()` now implements three-tier logic:
```python
# Priority: out_of_range > borderline > healthy
- out_of_range: Any value outside [min, borderline_max] or HR outside [min, max]
- borderline: Any BP in (max, borderline_max] (but no out_of_range values)
- healthy: All values in [min, max]
```

### 3. i18n Translations

#### English ([en/translation.json](frontend/src/i18n/locales/en/translation.json))
```json
"superAdmin.threshold.borderline": "Borderline Upper"
"superAdmin.threshold.validation.borderlineOrder": 
  "Borderline upper must be greater than upper bound."
```

#### Chinese ([zh/translation.json](frontend/src/i18n/locales/zh/translation.json))
```json
"superAdmin.threshold.borderline": "临界上限"
"superAdmin.threshold.validation.borderlineOrder": 
  "临界上限必须大于上限。"
```

### 4. Initialization Script
[init_thresholds.py](scripts/init_thresholds.py) already had correct structure:
```python
payload = {
    "systolic": {"min": 90, "max": 120, "borderline_max": 140},
    "diastolic": {"min": 60, "max": 80, "borderline_max": 90},
    "heart_rate": {"min": 60, "max": 100}
}
```

## Testing

### New Test Suite
Created [test_three_tier_validation.py](tests/threshold/test_three_tier_validation.py) with 9 tests:

1. ✅ Valid config with borderline_max passes
2. ✅ Missing borderline_max for BP raises error
3. ✅ borderline_max <= max raises error
4. ✅ borderline_max > hard limit raises error
5. ✅ Values in [min, max] are healthy
6. ✅ Values in (max, borderline_max] are borderline
7. ✅ Values outside all ranges are out_of_range
8. ✅ out_of_range takes precedence over borderline
9. ✅ Heart rate has no borderline zone

### Test Results
```
All 52 tests passed (43 existing + 9 new)
✅ No regressions
✅ All validation logic working correctly
✅ Status computation follows three-tier model
```

## Migration Notes

### For Existing Deployments

1. **Update Active Config**: Current configs without `borderline_max` will need updating:
   ```bash
   # Option 1: Re-run init script (if no custom config exists)
   python scripts/init_thresholds.py
   
   # Option 2: Update via Super Admin UI after deployment
   ```

2. **Backward Compatibility**: The `_compute_status` method gracefully handles old configs:
   ```python
   s_range.get("borderline_max", s_range["max"])
   # Falls back to max if borderline_max is missing
   ```

3. **Frontend Validation**: Form now requires all 3 values for BP metrics before saving.

## API Contract

### Request Format (POST /api/v1/superadmin/thresholds/draft)
```json
{
  "thresholds": {
    "systolic": {
      "min": 90,
      "max": 120,
      "borderline_max": 140
    },
    "diastolic": {
      "min": 60,
      "max": 80,
      "borderline_max": 90
    },
    "heart_rate": {
      "min": 60,
      "max": 100
    }
  }
}
```

### Response Format (GET /api/v1/thresholds/active)
```json
{
  "version": 1,
  "thresholds": {
    "systolic": {
      "min": 90,
      "max": 120,
      "borderline_max": 140
    },
    ...
  },
  "updated_at": "2025-12-18T10:30:00Z",
  "updated_by": "admin@example.com"
}
```

## User Guide

### For Super Admins

1. Navigate to **Super Admin Setting**
2. Configure three values for each BP metric:
   - **Lower Bound**: Minimum healthy value
   - **Upper Bound**: Maximum healthy value
   - **Borderline Upper**: Maximum acceptable value before out of range
3. Configure two values for heart rate (no borderline)
4. Click **Save Draft** to preview impact
5. Review preview showing status changes
6. Click **Publish** to activate

### Validation Rules
- Lower < Upper < Borderline (for BP)
- Lower < Upper (for heart rate)
- All values within hard limits (30-250 for BP, 30-150 for HR)

## Next Steps

1. ✅ Frontend form with 3 fields per BP metric
2. ✅ Backend validation for borderline_max
3. ✅ Three-tier status computation
4. ✅ i18n translations
5. ✅ Comprehensive test coverage
6. 🔲 Update dashboard to display borderline status with orange color
7. 🔲 Update HealthChart.js to use dynamic thresholds
8. 🔲 E2E tests for complete flow

## Files Modified

1. `frontend/src/pages/SuperAdminSettings.js` - Form UI & validation
2. `frontend/src/i18n/locales/en/translation.json` - English labels
3. `frontend/src/i18n/locales/zh/translation.json` - Chinese labels
4. `src/manager/threshold_manager.py` - Validation & status logic
5. `tests/threshold/test_three_tier_validation.py` - New test suite (created)

## References
- User Request: Senior Full-Stack Developer implementing three-tier threshold
- Issue: Frontend sent `{lower, upper}` but backend expected `{min, max, borderline_max}`
- Solution: Aligned frontend payload structure with backend expectations
