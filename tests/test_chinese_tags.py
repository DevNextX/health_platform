"""
Test Chinese character tag filtering functionality
"""
import json
import pytest
from datetime import datetime


class TestChineseTagFiltering:
    """Test Chinese character support in tag filtering"""
    
    def test_create_records_with_chinese_tags(self, client, auth_headers):
        """Test creating health records with Chinese tags"""
        access_headers = auth_headers['access']
        
        # Create records with Chinese tags as mentioned in requirements
        records = [
            {
                'systolic': 120, 'diastolic': 80, 'heart_rate': 72,
                'tags': ['晨起', '家里'], 'note': '早晨起床后测量'
            },
            {
                'systolic': 135, 'diastolic': 85, 'heart_rate': 78,
                'tags': ['运动后', '健身房'], 'note': '跑步后30分钟测量'
            },
            {
                'systolic': 125, 'diastolic': 82, 'heart_rate': 70,
                'tags': ['服药前', '晨起'], 'note': '服药前测量'
            }
        ]
        
        created_ids = []
        for record in records:
            response = client.post('/api/v1/health', json=record, headers=access_headers)
            assert response.status_code == 201
            created_ids.append(response.get_json()['id'])
        
        # Ensure records were created successfully
        assert len(created_ids) == 3
    
    def test_filter_by_chinese_tags(self, client, auth_headers):
        """Test filtering health records by Chinese tags"""
        access_headers = auth_headers['access']
        
        # Create test records first
        self.test_create_records_with_chinese_tags(client, auth_headers)
        
        # Test filtering by '晨起' tag - should return 2 records
        response = client.get('/api/v1/health?tags=晨起', headers=access_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'records' in data
        assert len(data['records']) == 2
        
        # Verify the returned records contain the '晨起' tag
        for record in data['records']:
            assert '晨起' in record['tags']
    
    def test_filter_by_multiple_chinese_tags(self, client, auth_headers):
        """Test filtering by multiple Chinese tags"""
        access_headers = auth_headers['access']
        
        # Create test records first
        self.test_create_records_with_chinese_tags(client, auth_headers)
        
        # Test filtering by multiple tags
        response = client.get('/api/v1/health?tags=运动后,服药前', headers=access_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['records']) == 2  # Should match records with either tag
        
        # Verify each record contains at least one of the search tags
        for record in data['records']:
            assert ('运动后' in record['tags']) or ('服药前' in record['tags'])
    
    def test_chinese_notes(self, client, auth_headers):
        """Test Chinese characters in notes field"""
        access_headers = auth_headers['access']
        
        record_data = {
            'systolic': 130, 'diastolic': 83, 'heart_rate': 75,
            'tags': ['测试'], 'note': '这是一个中文备注测试'
        }
        
        response = client.post('/api/v1/health', json=record_data, headers=access_headers)
        assert response.status_code == 201
        
        data = response.get_json()
        assert data['note'] == '这是一个中文备注测试'
        assert data['tags'] == ['测试']
    
    def test_tag_filtering_no_results(self, client, auth_headers):
        """Test tag filtering when no records match"""
        access_headers = auth_headers['access']
        
        # Create some records
        self.test_create_records_with_chinese_tags(client, auth_headers)
        
        # Search for a tag that doesn't exist
        response = client.get('/api/v1/health?tags=不存在的标签', headers=access_headers)
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['records']) == 0
        assert data['pagination']['total'] == 0
    
    def test_mixed_language_tags(self, client, auth_headers):
        """Test records with mixed Chinese and English tags"""
        access_headers = auth_headers['access']
        
        record_data = {
            'systolic': 118, 'diastolic': 79, 'heart_rate': 68,
            'tags': ['morning', '晨起', 'home', '家里'], 
            'note': 'Mixed language test 混合语言测试'
        }
        
        response = client.post('/api/v1/health', json=record_data, headers=access_headers)
        assert response.status_code == 201
        
        # Test filtering by Chinese tag
        response = client.get('/api/v1/health?tags=晨起', headers=access_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['records']) >= 1
        
        # Test filtering by English tag
        response = client.get('/api/v1/health?tags=morning', headers=access_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['records']) >= 1