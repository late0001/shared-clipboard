#!/usr/bin/env python3
"""
运行共享剪贴板应用
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 启动共享剪贴板服务...")
    print("📌 访问地址: http://localhost:8000")
    print("📌 在同一网络下的其他设备访问此IP地址即可共享")
    print("📌 按 Ctrl+C 停止服务")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )