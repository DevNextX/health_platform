# 健康记录平台 - 管理员命令参考

## 🔍 状态检查
```bash
# 快速状态检查
./check_services.sh

# 检查进程
ps aux | grep -E "(flask|react-scripts)" | grep -v grep

# 检查端口
ss -tln | grep -E ":3000|:5000"

# 测试API
curl http://localhost:5000/api/healthz
curl http://localhost:3000
```

## 📝 日志查看
```bash
# 查看完整日志
cat logs/backend.log
cat logs/frontend.log

# 实时监控
tail -f logs/backend.log
tail -f logs/frontend.log

# 查看最近日志
tail -20 logs/backend.log
tail -20 logs/frontend.log

# 搜索错误
grep -i "error\|exception" logs/backend.log
grep -i "error\|exception" logs/frontend.log
```

## 🔄 服务管理
```bash
# 如果服务停止，重新启动:

# 后端 (新终端1)
source .venv/bin/activate
export PYTHONPATH=.
export FLASK_APP=src.app
python -m flask run --host=0.0.0.0 --port=5000 2>&1 | tee logs/backend.log

# 前端 (新终端2)  
cd frontend
npm start 2>&1 | tee ../logs/frontend.log
```

## 🧪 测试服务
```bash
# 运行后端测试
source .venv/bin/activate
python -m pytest -q

# 运行E2E测试 (需要服务运行)
cd tests/e2e
npm install
npx playwright install --with-deps
npm run test
```

## 📊 性能监控
```bash
# 查看资源使用
top -p $(pgrep -f "flask|react-scripts")

# 查看网络连接
netstat -tlnp | grep -E ":3000|:5000"
```
