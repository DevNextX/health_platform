#!/usr/bin/env python3
"""
前端连接性测试脚本
"""
import requests
import json

def test_frontend_connectivity():
    print("🔍 前端服务连接性测试")
    print("=" * 40)
    
    try:
        print("正在连接到 http://localhost:3000...")
        response = requests.get("http://localhost:3000", timeout=10)
        
        if response.status_code == 200:
            print("✅ 前端服务连接成功!")
            print(f"   状态码: {response.status_code}")
            print(f"   内容类型: {response.headers.get('content-type', 'unknown')}")
            
            # Check if it contains React content
            if 'text/html' in response.headers.get('content-type', ''):
                content = response.text[:500]  # First 500 chars
                if 'react' in content.lower() or 'root' in content:
                    print("✅ 确认是React应用页面")
                else:
                    print("⚠️ 页面内容可能不是预期的React应用")
            
            print("\n🧪 修复验证:")
            print("现在您可以安全地在浏览器中测试以下场景：")
            print("1. 访问: http://localhost:3000")  
            print("2. 注册/登录一个测试账户")
            print("3. 进入'健康记录'页面")
            print("4. 点击'添加记录'按钮")
            print("5. 在收缩压字段输入 '10' - 页面应该不再卡死")
            print("6. 在舒张压字段输入 '20' - 应该显示收缩压>舒张压的验证错误")
            print("7. 修正为有效值如 '120/80' - 应该能正常保存")
            
            print("\n✅ 修复要点:")
            print("- 移除了可能导致无限循环的表单验证逻辑")
            print("- 简化了自定义验证函数")  
            print("- 移除了保存按钮的禁用状态控制")
            print("- 保留了Ant Design原生的表单验证机制")
            
        else:
            print(f"❌ 前端服务返回异常状态码: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到前端服务")
        print("💡 请确保运行了: cd frontend && npm start")
        
    except requests.exceptions.Timeout:
        print("❌ 连接超时") 
        print("💡 前端服务可能正在启动中，请稍等片刻")
        
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")

if __name__ == "__main__":
    test_frontend_connectivity()