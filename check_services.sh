#!/bin/bash
echo "=== 健康记录平台服务状态检查 ==="
echo "检查时间: $(date)"
echo ""

echo "1. 进程状态:"
ps aux | grep -E "(flask|react-scripts)" | grep -v grep || echo "   没有找到运行的服务"

echo ""
echo "2. 端口监听状态:"
ss -tln | grep -E ":3000|:5000" || echo "   端口3000和5000未在监听"

echo ""
echo "3. 服务响应测试:"
if curl -s --connect-timeout 5 http://localhost:5000/api/healthz > /dev/null; then
    echo "   ✅ 后端 (5000): 正常响应"
else
    echo "   ❌ 后端 (5000): 无响应"
fi

if curl -s --connect-timeout 5 http://localhost:3000 > /dev/null; then
    echo "   ✅ 前端 (3000): 正常响应"
else
    echo "   ❌ 前端 (3000): 无响应"
fi

echo ""
echo "4. 日志文件状态:"
if [ -f "logs/backend.log" ]; then
    echo "   后端日志: $(wc -l < logs/backend.log) 行"
else
    echo "   后端日志: 不存在"
fi

if [ -f "logs/frontend.log" ]; then
    echo "   前端日志: $(wc -l < logs/frontend.log) 行"
else
    echo "   前端日志: 不存在"
fi

echo ""
echo "5. 最近的错误 (如果有):"
if [ -f "logs/backend.log" ]; then
    grep -i "error\|exception\|traceback" logs/backend.log | tail -3 || echo "   后端: 没有发现错误"
fi
