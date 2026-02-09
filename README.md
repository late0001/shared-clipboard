# 共享剪贴板应用

一个基于FastAPI的实时共享剪贴板应用，支持多设备同步。

## 功能特性

- 📋 实时剪贴板同步
- 🌐 WebSocket实时更新
- 📱 多设备支持
- 📊 使用统计展示
- 🔄 历史记录查看
- 💾 自动保存
- 📝 文本内容共享

## 环境
Python 3.12.9

## 安装与运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```
### 2. 运行应用
```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```
### 3. 访问应用
- 主页面：http://localhost:8000
- API文档：http://localhost:8000/docs
- 实时WebSocket：ws://localhost:8000/api/clipboard/ws

API端点
#### 剪贴板操作
- GET /api/clipboard/items - 获取剪贴板项目
- POST /api/clipboard/items - 创建新项目
- GET /api/clipboard/items/{id} - 获取特定项目
- PUT /api/clipboard/items/{id} - 更新项目
- DELETE /api/clipboard/items/{id} - 删除项目

#### 历史记录
- GET /api/clipboard/history/{item_id} - 获取项目历史

#### 同步
- POST /api/clipboard/sync - 同步剪贴板内容
- GET /api/clipboard/ws - WebSocket连接（实时更新）

#### 统计
- GET /api/clipboard/stats - 获取使用统计
#### 部署说明
使用Docker部署
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```
#### 环境变量
```bash
DATABASE_URL=sqlite+aiosqlite:///./clipboard.db
```
#### 安全建议
1. 生产环境应配置HTTPS
2. 添加用户认证
3. 限制访问IP
4. 定期备份数据库
5. 设置内容长度限制

#### 浏览器支持
- Chrome 58+
- Firefox 54+
- Safari 11+
- Edge 16+

#### 许可证

MIT License
## 扩展功能(未完善)

1. **用户认证**：添加JWT认证
2. **权限管理**：私有/公共剪贴板
3. **文件上传**：支持图片和文件
4. **加密传输**：端到端加密
5. **移动应用**：开发移动客户端
6. **云同步**：集成云存储
7. **OCR功能**：图片文字识别

这个共享剪贴板应用提供了一个完整的解决方案，包括后端API、WebSocket实时通信、前端界面和数据库存储。您可以根据需要进一步扩展功能。