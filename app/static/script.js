class SharedClipboard {
    constructor() {
        this.apiBase = '/api/clipboard';
        this.ws = null;
        this.deviceName = localStorage.getItem('clipboard_device') || '';
        this.lastSync = null;
        
        this.init();
    }
    
    async init() {
        // 设置设备名称
        if (this.deviceName) {
            document.getElementById('deviceName').value = this.deviceName;
        }
        
        // 监听设备名称变化
        document.getElementById('deviceName').addEventListener('change', (e) => {
            this.deviceName = e.target.value;
            localStorage.setItem('clipboard_device', this.deviceName);
        });
        
        // 加载统计数据
        await this.loadStats();
        
        // 加载最新内容
        await this.loadLatest();
        
        // 连接WebSocket
        this.connectWebSocket();
        
        // 设置自动保存
        this.setupAutoSave();
        
        // 监听粘贴事件
        document.addEventListener('paste', this.handlePaste.bind(this));
    }
    
    async loadStats() {
        try {
            const response = await fetch(`${this.apiBase}/stats`);
            const data = await response.json();
            
            document.getElementById('totalItems').textContent = data.total_items;
            document.getElementById('recentItems').textContent = data.recent_items_24h;
            document.getElementById('activeConnections').textContent = data.active_connections;
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }
    
    async loadLatest() {
        try {
            const response = await fetch(`${this.apiBase}/items?limit=10`);
            const items = await response.json();
            
            // 如果有最新项目，显示第一个
            if (items && items.length > 0) {
                const latest = items[0];
                document.getElementById('clipboardContent').value = latest.content;
                this.showNotification('已加载最新内容');
            }
            
            // 更新历史记录列表
            this.updateHistoryList(items);
        } catch (error) {
            console.error('Failed to load latest:', error);
        }
    }
    
    updateHistoryList(items) {
        const historyList = document.getElementById('historyList');
        historyList.innerHTML = '';
        
        if (!items || items.length === 0) {
            historyList.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">暂无历史记录</p>';
            return;
        }
        
        items.forEach(item => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.onclick = () => this.selectHistoryItem(item);
            
            const content = item.content.length > 100 
                ? item.content.substring(0, 100) + '...' 
                : item.content;
            
            const time = new Date(item.updated_at).toLocaleString();
            
            historyItem.innerHTML = `
                <div class="history-content">${this.escapeHtml(content)}</div>
                <div class="history-meta">
                    <span><i class="fas fa-laptop"></i> ${item.device_name || '未知设备'}</span>
                    <span><i class="far fa-clock"></i> ${time}</span>
                </div>
            `;
            
            historyList.appendChild(historyItem);
        });
    }
    
    selectHistoryItem(item) {
        document.getElementById('clipboardContent').value = item.content;
        this.showNotification('已选择历史记录');
    }
    
    async saveToClipboard() {
        const content = document.getElementById('clipboardContent').value.trim();
        
        if (!content) {
            this.showNotification('请输入内容', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/items`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content,
                    device_name: this.deviceName
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.showNotification('内容已共享！');
                
                // 复制到系统剪贴板
                if (navigator.clipboard) {
                    await navigator.clipboard.writeText(content);
                }
                
                // 更新历史记录
                await this.loadLatest();
            } else {
                throw new Error('保存失败');
            }
        } catch (error) {
            console.error('Failed to save:', error);
            this.showNotification('保存失败', 'error');
        }
    }
    
    async clearClipboard() {
        if (!confirm('确定要清空剪贴板内容吗？')) {
            return;
        }
        
        document.getElementById('clipboardContent').value = '';
        this.showNotification('已清空');
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/clipboard/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            this.updateConnectionStatus(true);
            console.log('WebSocket连接已建立');
        };
        
        this.ws.onclose = () => {
            this.updateConnectionStatus(false);
            console.log('WebSocket连接已断开，5秒后重连...');
            
            // 5秒后重连
            setTimeout(() => this.connectWebSocket(), 5000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket错误:', error);
        };
        
        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            } catch (error) {
                console.error('解析WebSocket消息失败:', error);
            }
        };
    }
    
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'new':
                this.showNotification('有新内容共享！');
                this.loadLatest();
                this.loadStats();
                break;
                
            case 'update':
                this.showNotification('内容已更新');
                this.loadLatest();
                break;
                
            case 'delete':
                this.loadLatest();
                this.loadStats();
                break;
        }
    }
    
    updateConnectionStatus(connected) {
        const indicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        
        if (connected) {
            indicator.className = 'status-indicator connected';
            statusText.textContent = '已连接 (实时更新)';
        } else {
            indicator.className = 'status-indicator';
            statusText.textContent = '连接断开，尝试重连...';
        }
    }
    
    showNotification(message, type = 'success') {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification show ${type}`;
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
    
    setupAutoSave() {
        let saveTimeout;
        const textarea = document.getElementById('clipboardContent');
        
        textarea.addEventListener('input', () => {
            if (saveTimeout) {
                clearTimeout(saveTimeout);
            }
            
            // 防抖：停止输入2秒后自动保存
            saveTimeout = setTimeout(() => {
                const content = textarea.value.trim();
                if (content) {
                    this.autoSave(content);
                }
            }, 2000);
        });
    }
    
    async autoSave(content) {
        try {
            await fetch(`${this.apiBase}/items`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content,
                    device_name: this.deviceName,
                    content_type: 'text'
                })
            });
        } catch (error) {
            console.error('Auto-save failed:', error);
        }
    }
    
    handlePaste(event) {
        const pastedText = event.clipboardData.getData('text');
        if (pastedText) {
            // 可以在这里添加自动上传逻辑
            console.log('检测到粘贴:', pastedText);
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.clipboard = new SharedClipboard();
});

// 全局函数供按钮调用
function saveToClipboard() {
    if (window.clipboard) {
        window.clipboard.saveToClipboard();
    }
}

function clearClipboard() {
    if (window.clipboard) {
        window.clipboard.clearClipboard();
    }
}

function loadLatest() {
    if (window.clipboard) {
        window.clipboard.loadLatest();
    }
}