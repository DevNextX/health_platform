#!/usr/bin/env python3
"""
Quick API validation test script
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_validation_api():
    import time
    timestamp = int(time.time())
    
    # Register a test user with unique email
    register_data = {
        "username": f"test_user_{timestamp}",
        "email": f"test_{timestamp}@example.com", 
        "password": "TestPassword123!",
        "age": 30,
        "gender": "M",
        "weight": 70
    }
    
    print("1. Registering test user...")
    resp = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
    print(f"Register status: {resp.status_code}")
    
    if resp.status_code not in [200, 201]:
        print(f"Register failed: {resp.text}")
        return
    
    # Login to get token
    login_data = {
        "email": register_data["email"],
        "password": "TestPassword123!"
    }
    
    print("\n2. Logging in...")
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"Login status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
        
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test cases for new validation rules
    test_cases = [
        {
            "name": "血压过低 (systolic=25)",
            "data": {"systolic": 25, "diastolic": 80, "heart_rate": 72},
            "expected_status": 400
        },
        {
            "name": "血压过高 (systolic=260)", 
            "data": {"systolic": 260, "diastolic": 80, "heart_rate": 72},
            "expected_status": 400
        },
        {
            "name": "心率过高 (heart_rate=160)",
            "data": {"systolic": 120, "diastolic": 80, "heart_rate": 160}, 
            "expected_status": 400
        },
        {
            "name": "收缩压等于舒张压",
            "data": {"systolic": 80, "diastolic": 80, "heart_rate": 72},
            "expected_status": 400
        },
        {
            "name": "收缩压小于舒张压", 
            "data": {"systolic": 70, "diastolic": 80, "heart_rate": 72},
            "expected_status": 400
        },
        {
            "name": "有效数据 (边界值)",
            "data": {"systolic": 31, "diastolic": 30, "heart_rate": 30},
            "expected_status": 201
        },
        {
            "name": "心率为空 (应允许)",
            "data": {"systolic": 120, "diastolic": 80},
            "expected_status": 201
        }
    ]
    
    print("\n3. Testing validation rules:")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['name']}")
        resp = requests.post(f"{BASE_URL}/api/v1/health", json=test_case['data'], headers=headers)
        
        status_match = "✅" if resp.status_code == test_case['expected_status'] else "❌"
        print(f"状态码: {resp.status_code} (期望: {test_case['expected_status']}) {status_match}")
        
        if resp.status_code != test_case['expected_status']:
            print(f"响应内容: {resp.text}")
        elif resp.status_code >= 400:
            try:
                error_msg = resp.json()
                print(f"错误信息: {error_msg}")
            except:
                print(f"响应内容: {resp.text}")

if __name__ == "__main__":
    test_validation_api()