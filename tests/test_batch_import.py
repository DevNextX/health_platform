"""
Test cases for batch import health records functionality.
"""
import pytest
from io import BytesIO
import pandas as pd
from datetime import datetime


class TestBatchImport:
    """Test batch import related endpoints"""
    
    def test_batch_import_csv_success(self, client, auth_headers):
        """Test successful batch import with CSV file"""
        access_headers = auth_headers['access']
        
        # Create a CSV file in memory
        csv_content = """成员名称,测量时间,收缩压,舒张压,心率,标签,备注
Self,2025-12-19 08:30:00,120,80,72,晨起;空腹,早晨测量
Self,2025-12-18 20:00:00,135,85,78,晚餐后,感觉有点头晕"""
        
        data = {
            'file': (BytesIO(csv_content.encode('utf-8-sig')), 'test_import.csv')
        }
        
        response = client.post('/api/v1/health/batch-import', 
                               data=data,
                               headers=access_headers,
                               content_type='multipart/form-data')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert result['summary']['total_rows'] == 2
        assert result['summary']['success_count'] == 2
        assert result['summary']['error_count'] == 0
    
    def test_batch_import_xlsx_success(self, client, auth_headers):
        """Test successful batch import with Excel file"""
        access_headers = auth_headers['access']
        
        # Create an Excel file in memory
        df = pd.DataFrame({
            '成员名称': ['Self', 'Self'],
            '测量时间': ['2025-12-19 08:30:00', '2025-12-18 20:00:00'],
            '收缩压': [120, 135],
            '舒张压': [80, 85],
            '心率': [72, 78],
            '标签': ['晨起;空腹', '晚餐后'],
            '备注': ['早晨测量', '感觉有点头晕']
        })
        
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        
        data = {
            'file': (excel_buffer, 'test_import.xlsx')
        }
        
        response = client.post('/api/v1/health/batch-import',
                               data=data,
                               headers=access_headers,
                               content_type='multipart/form-data')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert result['summary']['success_count'] == 2
    
    def test_batch_import_english_headers(self, client, auth_headers):
        """Test batch import with English column headers"""
        access_headers = auth_headers['access']
        
        csv_content = """Member Name,Timestamp,Systolic,Diastolic,Heart Rate,Tags,Note
Self,2025-12-19 08:30:00,120,80,72,morning;fasting,Morning measurement"""
        
        data = {
            'file': (BytesIO(csv_content.encode('utf-8-sig')), 'test_english.csv')
        }
        
        response = client.post('/api/v1/health/batch-import',
                               data=data,
                               headers=access_headers,
                               content_type='multipart/form-data')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['summary']['success_count'] == 1
    
    def test_batch_import_missing_file(self, client, auth_headers):
        """Test batch import without file"""
        access_headers = auth_headers['access']
        
        response = client.post('/api/v1/health/batch-import',
                               headers=access_headers)
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'No file provided' in result['message']
    
    def test_batch_import_invalid_file_type(self, client, auth_headers):
        """Test batch import with invalid file type"""
        access_headers = auth_headers['access']
        
        data = {
            'file': (BytesIO(b'invalid content'), 'test.txt')
        }
        
        response = client.post('/api/v1/health/batch-import',
                               data=data,
                               headers=access_headers,
                               content_type='multipart/form-data')
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'Only .xlsx and .csv files are supported' in result['message']
    
    def test_batch_import_file_too_large(self, client, auth_headers):
        """Test batch import with file exceeding size limit"""
        access_headers = auth_headers['access']
        
        # Create a file larger than 5MB
        large_content = 'a' * (6 * 1024 * 1024)
        data = {
            'file': (BytesIO(large_content.encode('utf-8')), 'large.csv')
        }
        
        response = client.post('/api/v1/health/batch-import',
                               data=data,
                               headers=access_headers,
                               content_type='multipart/form-data')
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'File size exceeds 5MB limit' in result['message']
    
    def test_batch_import_missing_required_columns(self, client, auth_headers):
        """Test batch import with missing required columns"""
        access_headers = auth_headers['access']
        
        csv_content = """成员名称,测量时间
Self,2025-12-19 08:30:00"""
        
        data = {
            'file': (BytesIO(csv_content.encode('utf-8-sig')), 'missing_cols.csv')
        }
        
        response = client.post('/api/v1/health/batch-import',
                               data=data,
                               headers=access_headers,
                               content_type='multipart/form-data')
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'Missing required column' in result['message']
    
    def test_batch_import_validation_errors(self, client, auth_headers):
        """Test batch import with validation errors"""
        access_headers = auth_headers['access']
        
        # CSV with various validation errors
        csv_content = """成员名称,测量时间,收缩压,舒张压,心率
Self,2025-12-19 08:30:00,25,80,72
Self,2025-12-19 09:00:00,120,125,78
Self,2025-12-19 10:00:00,120,80,160"""
        
        data = {
            'file': (BytesIO(csv_content.encode('utf-8-sig')), 'validation_errors.csv')
        }
        
        response = client.post('/api/v1/health/batch-import',
                               data=data,
                               headers=access_headers,
                               content_type='multipart/form-data')
        
        assert response.status_code == 200
        result = response.get_json()
        # All three rows should have errors
        assert result['summary']['error_count'] == 3
        assert result['summary']['success_count'] == 0
    
    def test_batch_import_member_not_found(self, client, auth_headers):
        """Test batch import with non-existent member"""
        access_headers = auth_headers['access']
        
        csv_content = """成员名称,测量时间,收缩压,舒张压
不存在的成员,2025-12-19 08:30:00,120,80"""
        
        data = {
            'file': (BytesIO(csv_content.encode('utf-8-sig')), 'invalid_member.csv')
        }
        
        response = client.post('/api/v1/health/batch-import',
                               data=data,
                               headers=access_headers,
                               content_type='multipart/form-data')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['summary']['error_count'] == 1
        assert 'not found' in result['errors'][0]['errors'][0]
    
    def test_batch_import_self_aliases(self, client, auth_headers):
        """Test batch import with different Self aliases (Self/自己/本人)"""
        access_headers = auth_headers['access']
        
        csv_content = """成员名称,测量时间,收缩压,舒张压
Self,2025-12-19 08:30:00,120,80
自己,2025-12-19 09:00:00,125,82
本人,2025-12-19 10:00:00,118,78"""
        
        data = {
            'file': (BytesIO(csv_content.encode('utf-8-sig')), 'self_aliases.csv')
        }
        
        response = client.post('/api/v1/health/batch-import',
                               data=data,
                               headers=access_headers,
                               content_type='multipart/form-data')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['summary']['success_count'] == 3
    
    def test_batch_import_max_records_limit(self, client, auth_headers):
        """Test batch import exceeding 1000 records limit"""
        access_headers = auth_headers['access']
        
        # Create a DataFrame with 1001 rows
        df = pd.DataFrame({
            '成员名称': ['Self'] * 1001,
            '测量时间': [f'2025-12-{i%28 + 1:02d} 08:30:00' for i in range(1001)],
            '收缩压': [120] * 1001,
            '舒张压': [80] * 1001
        })
        
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        csv_buffer.seek(0)
        
        data = {
            'file': (csv_buffer, 'too_many_records.csv')
        }
        
        response = client.post('/api/v1/health/batch-import',
                               data=data,
                               headers=access_headers,
                               content_type='multipart/form-data')
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'Maximum 1000 records' in result['message']
    
    def test_batch_import_timezone_handling(self, client, auth_headers):
        """Test batch import with different timezone formats"""
        access_headers = auth_headers['access']
        
        # Test with and without timezone info
        csv_content = """成员名称,测量时间,收缩压,舒张压
Self,2025-12-19 08:30:00,120,80
Self,2025-12-19T09:00:00+08:00,125,82"""
        
        data = {
            'file': (BytesIO(csv_content.encode('utf-8-sig')), 'timezone_test.csv')
        }
        
        response = client.post('/api/v1/health/batch-import',
                               data=data,
                               headers=access_headers,
                               content_type='multipart/form-data')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['summary']['success_count'] == 2
    
    def test_batch_import_optional_fields(self, client, auth_headers):
        """Test batch import with optional fields (heart_rate, tags, note)"""
        access_headers = auth_headers['access']
        
        # Test with all optional fields present and some missing
        csv_content = """成员名称,测量时间,收缩压,舒张压,心率,标签,备注
Self,2025-12-19 08:30:00,120,80,72,晨起;空腹,早晨测量
Self,2025-12-19 09:00:00,125,82,,,"""
        
        data = {
            'file': (BytesIO(csv_content.encode('utf-8-sig')), 'optional_fields.csv')
        }
        
        response = client.post('/api/v1/health/batch-import',
                               data=data,
                               headers=access_headers,
                               content_type='multipart/form-data')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['summary']['success_count'] == 2
    
    def test_batch_import_unauthorized(self, client):
        """Test batch import without authorization"""
        csv_content = """成员名称,测量时间,收缩压,舒张压
Self,2025-12-19 08:30:00,120,80"""
        
        data = {
            'file': (BytesIO(csv_content.encode('utf-8-sig')), 'test.csv')
        }
        
        response = client.post('/api/v1/health/batch-import',
                               data=data,
                               content_type='multipart/form-data')
        
        assert response.status_code == 401
