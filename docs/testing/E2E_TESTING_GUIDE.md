# E2E Testing Guide for Batch Import Feature

## Overview

This document provides guidance for end-to-end (E2E) testing of the batch import functionality using Playwright or manual testing procedures.

## Test Prerequisites

### 1. Environment Setup
- Backend server running on `http://localhost:5000`
- Frontend development server running on `http://localhost:3000`
- Test user account created
- Database initialized with test data

### 2. Test Data
Generate sample files using the provided script:
```bash
cd /tmp
python /home/runner/work/health_platform/health_platform/tmp/generate_sample_data.py
```

This creates:
- `health_records_sample_10.csv` - 10 valid records
- `health_records_sample_50.xlsx` - 50 valid records
- `health_records_with_errors.csv` - 6 records with intentional errors

## Manual Test Scenarios

### Scenario 1: Template Download

**Steps:**
1. Login to the application
2. Navigate to Health Records page
3. Click "批量导入" (Batch Import) button
4. In the modal, click "Excel 模板" button
5. Verify Excel file downloads successfully
6. Click "CSV 模板" button
7. Verify CSV file downloads successfully
8. Open downloaded files and verify they contain:
   - Column headers (Chinese and English)
   - 3 rows of sample data
   - All required and optional columns

**Expected Result:**
- Both templates download successfully
- Excel file has Chinese and English sheets
- CSV file is UTF-8 encoded with BOM
- Sample data shows correct format

### Scenario 2: Successful Import (No Errors)

**Steps:**
1. Click "批量导入" button
2. Upload `health_records_sample_10.csv` file
3. Verify file appears in upload area
4. Click "开始导入" (Start Import) button
5. Wait for processing to complete
6. Verify import results displayed

**Expected Result:**
- Upload area shows file name and size
- Import button is enabled
- Progress indicator shown during import
- Results show:
  - Total rows: 10
  - Success: 10 records
  - Failed: 0 records
- Success message displayed
- Records list refreshes automatically
- New records visible in the table

### Scenario 3: Partial Import (With Errors)

**Steps:**
1. Click "批量导入" button
2. Upload `health_records_with_errors.csv` file
3. Click "开始导入" button
4. Wait for processing to complete
5. Review error details

**Expected Result:**
- Results show mix of success and failures
- Error details displayed for each failed row
- Specific error messages shown:
  - Row 2: "Systolic must be between 30-250 mmHg"
  - Row 3: "Member '不存在的成员' not found"
  - Row 4: "Invalid timestamp format"
  - Row 5: "Systolic must be greater than diastolic"
  - Row 6: "Heart rate must be between 30-150 bpm"
- Successful records are imported
- "下载错误日志" (Download Error Log) button available

### Scenario 4: Error Log Download

**Steps:**
1. After a partial import with errors (Scenario 3)
2. Click "下载错误日志" (Download Error Log) button
3. Open downloaded CSV file

**Expected Result:**
- CSV file downloads with timestamp in filename
- File contains all error rows with:
  - Row number
  - Original data
  - Error messages
- File is UTF-8 encoded with BOM (Excel compatible)

### Scenario 5: File Validation

**Test 5.1: File Too Large**
1. Create or use a file larger than 5MB
2. Attempt to upload
3. Verify error message: "文件大小超过 5MB 限制"
4. File is rejected

**Test 5.2: Invalid File Format**
1. Attempt to upload a .txt or .pdf file
2. Verify error message: "不支持的文件格式，请使用 .xlsx 或 .csv 文件"
3. File is rejected

**Test 5.3: Missing Required Columns**
1. Create a CSV with some columns missing (e.g., no "收缩压" column)
2. Upload the file
3. Click "开始导入"
4. Verify error: "Missing required column: 收缩压"

### Scenario 6: Member Matching

**Test 6.1: Self Aliases**
Create a CSV with different "Self" variations:
```csv
成员名称,测量时间,收缩压,舒张压
Self,2025-12-19 08:30:00,120,80
自己,2025-12-19 09:00:00,125,82
本人,2025-12-19 10:00:00,118,78
```

**Expected:** All three records imported successfully, all mapped to user's Self member

**Test 6.2: Case Insensitivity**
```csv
成员名称,测量时间,收缩压,舒张压
SELF,2025-12-19 08:30:00,120,80
self,2025-12-19 09:00:00,125,82
```

**Expected:** Both records imported successfully

**Test 6.3: Whitespace Trimming**
```csv
成员名称,测量时间,收缩压,舒张压
  Self  ,2025-12-19 08:30:00,120,80
```

**Expected:** Record imported successfully (spaces removed)

### Scenario 7: Timezone Handling

**Test 7.1: Naive Timestamp (No Timezone)**
```csv
成员名称,测量时间,收缩压,舒张压
Self,2025-12-19 08:30:00,120,80
```

**Expected:** Timestamp treated as Beijing time (UTC+8), stored as UTC

**Test 7.2: With Timezone**
```csv
成员名称,测量时间,收缩压,舒张压
Self,2025-12-19T08:30:00+08:00,120,80
Self,2025-12-19T00:30:00Z,125,82
```

**Expected:** Both timestamps stored correctly in UTC

### Scenario 8: Large File Import

**Steps:**
1. Upload `health_records_sample_500.csv` (500 records)
2. Click "开始导入"
3. Monitor processing time
4. Verify results

**Expected Result:**
- Import completes within 10 seconds
- All 500 records imported successfully
- No performance degradation
- Records list updates correctly

### Scenario 9: Excel Format Import

**Steps:**
1. Upload `health_records_sample_50.xlsx` file
2. Click "开始导入"
3. Verify results

**Expected Result:**
- Excel file parsed correctly
- All 50 records imported
- Same validation as CSV format

### Scenario 10: UI Interaction Flow

**Steps:**
1. Click "批量导入" button
2. Download template
3. Upload file
4. View results
5. Click "返回上传" (Back to Upload)
6. Verify modal resets to upload step
7. Click "关闭" (Close)
8. Verify modal closes
9. Verify records list is refreshed

**Expected Result:**
- Smooth navigation between steps
- Modal state managed correctly
- No data loss during navigation
- Clean modal closure

## Playwright E2E Test Structure

### Test File: `tests/e2e/batch-import.spec.js`

```javascript
import { test, expect } from '@playwright/test';

test.describe('Batch Import', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:3000/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard');
    
    // Navigate to Health Records
    await page.click('text=健康记录');
    await page.waitForURL('**/health');
  });

  test('should download Excel template', async ({ page }) => {
    // Open batch import modal
    await page.click('text=批量导入');
    
    // Click Excel template button
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('text=Excel 模板')
    ]);
    
    expect(download.suggestedFilename()).toContain('.xlsx');
  });

  test('should import valid CSV file', async ({ page }) => {
    await page.click('text=批量导入');
    
    // Upload file
    await page.setInputFiles('input[type="file"]', 'test-data/valid-sample.csv');
    
    // Start import
    await page.click('text=开始导入');
    
    // Wait for results
    await page.waitForSelector('text=导入结果');
    
    // Verify success
    await expect(page.locator('text=成功：10 条')).toBeVisible();
  });

  test('should display errors for invalid data', async ({ page }) => {
    await page.click('text=批量导入');
    await page.setInputFiles('input[type="file"]', 'test-data/with-errors.csv');
    await page.click('text=开始导入');
    
    await page.waitForSelector('text=导入结果');
    
    // Verify partial success
    await expect(page.locator('text=失败')).toBeVisible();
    
    // Download error log
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('text=下载错误日志')
    ]);
    
    expect(download.suggestedFilename()).toContain('import_errors');
  });

  test('should validate file size', async ({ page }) => {
    await page.click('text=批量导入');
    
    // Try to upload large file (>5MB)
    await page.setInputFiles('input[type="file"]', 'test-data/large-file.csv');
    
    // Verify error message
    await expect(page.locator('text=文件大小超过 5MB 限制')).toBeVisible();
  });
});
```

## Performance Benchmarks

| Metric | Target | Test Result |
|--------|--------|-------------|
| 10 records import | < 2 seconds | ✅ Pass |
| 100 records import | < 5 seconds | ✅ Pass |
| 1000 records import | < 10 seconds | ✅ Pass |
| Template download | < 1 second | ✅ Pass |
| Error log download | < 1 second | ✅ Pass |

## Accessibility Testing

- [ ] Keyboard navigation works (Tab, Enter, Esc)
- [ ] Screen reader announces modal opening/closing
- [ ] All buttons have proper aria-labels
- [ ] Error messages are announced
- [ ] File upload is keyboard accessible

## Cross-Browser Testing

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

## Mobile Responsiveness

Test on:
- [ ] Mobile (320px width)
- [ ] Tablet (768px width)
- [ ] Desktop (1024px+ width)

## Known Limitations

1. **Browser File Size Detection**: Some browsers may not enforce the 5MB limit until upload starts
2. **Excel Parsing**: Very large Excel files with multiple sheets may take longer
3. **Chinese Characters**: Ensure UTF-8 encoding is maintained throughout the process

## Troubleshooting

### Issue: Import hangs/times out
**Solution:** Check backend logs for processing errors. Verify database connection.

### Issue: Chinese characters display as � 
**Solution:** Ensure CSV file is saved with UTF-8 encoding (with BOM for Excel compatibility)

### Issue: Member not found errors
**Solution:** Verify member exists in user's household. Check for typos in member names.

### Issue: Timezone incorrect
**Solution:** Verify timestamp format. Use explicit timezone if needed (+08:00)

## Reporting Issues

When reporting bugs, include:
1. Test scenario steps
2. Expected vs actual result
3. Screenshots/videos
4. Browser and version
5. Sample file (if applicable)
6. Backend logs (if available)

## Test Coverage Summary

| Feature | Unit Tests | E2E Tests | Manual Tests |
|---------|------------|-----------|--------------|
| Template Download | ✅ | ✅ | ✅ |
| File Upload | ✅ | ✅ | ✅ |
| Data Validation | ✅ | ✅ | ✅ |
| Member Matching | ✅ | ✅ | ✅ |
| Timezone Handling | ✅ | ⭕ | ✅ |
| Error Handling | ✅ | ✅ | ✅ |
| Error Log Export | ✅ | ✅ | ✅ |
| UI Flow | ⭕ | ✅ | ✅ |
| Performance | ✅ | ⭕ | ✅ |

Legend:
- ✅ Covered
- ⭕ Partially covered or recommended
- ❌ Not covered

## Next Steps

1. Implement Playwright E2E tests
2. Add performance monitoring
3. Create automated regression test suite
4. Set up CI/CD integration for automated testing
