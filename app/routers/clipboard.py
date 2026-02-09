from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc
from typing import List
import json
import asyncio
from datetime import datetime, timedelta

from app.database import get_db
from app.models import ClipboardItem, ClipboardHistory
from app.schemas import (
    ClipboardItemCreate, 
    ClipboardItemUpdate, 
    ClipboardItemResponse,
    ClipboardSyncRequest
)

router = APIRouter(prefix="/api/clipboard", tags=["clipboard"])

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

manager = ConnectionManager()

@router.get("/items", response_model=List[ClipboardItemResponse])
async def get_clipboard_items(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """获取最新的剪贴板项目"""
    from sqlalchemy import select
    query = select(ClipboardItem).order_by(desc(ClipboardItem.updated_at)).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    return items

@router.get("/items/{item_id}", response_model=ClipboardItemResponse)
async def get_clipboard_item(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取特定剪贴板项目"""
    from sqlalchemy import select
    query = select(ClipboardItem).where(ClipboardItem.id == item_id)
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return item

@router.post("/items", response_model=ClipboardItemResponse)
async def create_clipboard_item(
    item: ClipboardItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新的剪贴板项目"""
    from sqlalchemy import select
    # 检查是否有相同内容的最新项目
    query = select(ClipboardItem).where(
        ClipboardItem.content == item.content
    ).order_by(desc(ClipboardItem.updated_at))
    
    result = await db.execute(query)
    existing_item = result.scalar_one_or_none()
    
    if existing_item:
        # 更新现有项目的时间戳
        existing_item.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing_item)
        
        # 广播更新
        await manager.broadcast({
            "type": "update",
            "data": existing_item.to_dict()
        })
        
        return existing_item
    
    # 创建新项目
    db_item = ClipboardItem(
        content=item.content,
        content_type=item.content_type,
        device_name=item.device_name
    )
    
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    
    # 广播新项目
    await manager.broadcast({
        "type": "new",
        "data": db_item.to_dict()
    })
    
    return db_item

@router.put("/items/{item_id}", response_model=ClipboardItemResponse)
async def update_clipboard_item(
    item_id: str,
    item_update: ClipboardItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新剪贴板项目"""
    from sqlalchemy import select
    query = select(ClipboardItem).where(ClipboardItem.id == item_id)
    result = await db.execute(query)
    db_item = result.scalar_one_or_none()
    
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # 更新内容
    db_item.content = item_update.content
    if item_update.content_type:
        db_item.content_type = item_update.content_type
    db_item.updated_at = datetime.utcnow()
    
    # 保存到历史记录
    history_item = ClipboardHistory(
        item_id=item_id,
        content=item_update.content
    )
    db.add(history_item)
    
    await db.commit()
    await db.refresh(db_item)
    
    # 广播更新
    await manager.broadcast({
        "type": "update",
        "data": db_item.to_dict()
    })
    
    return db_item

@router.delete("/items/{item_id}")
async def delete_clipboard_item(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除剪贴板项目"""
    from sqlalchemy import delete
    query = delete(ClipboardItem).where(ClipboardItem.id == item_id)
    result = await db.execute(query)
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # 广播删除
    await manager.broadcast({
        "type": "delete",
        "data": {"id": item_id}
    })
    
    return {"message": "Item deleted successfully"}

@router.get("/history/{item_id}")
async def get_clipboard_history(
    item_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """获取剪贴板项目的历史记录"""
    from sqlalchemy import select
    query = select(ClipboardHistory).where(
        ClipboardHistory.item_id == item_id
    ).order_by(desc(ClipboardHistory.timestamp)).limit(limit)
    
    result = await db.execute(query)
    history_items = result.scalars().all()
    
    return [
        {
            "id": item.id,
            "content": item.content,
            "timestamp": item.timestamp.isoformat() if item.timestamp else None
        }
        for item in history_items
    ]

@router.post("/sync")
async def sync_clipboard(
    sync_request: ClipboardSyncRequest,
    db: AsyncSession = Depends(get_db)
):
    """同步剪贴板内容"""
    from sqlalchemy import select
    query = select(ClipboardItem)
    
    if sync_request.last_sync:
        query = query.where(ClipboardItem.updated_at > sync_request.last_sync)
    
    query = query.order_by(desc(ClipboardItem.updated_at))
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "last_sync": datetime.utcnow(),
        "items": [item.to_dict() for item in items]
    }

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接用于实时更新"""
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/stats")
async def get_clipboard_stats(db: AsyncSession = Depends(get_db)):
    """获取剪贴板统计信息"""
    from sqlalchemy import func, select
    
    # 总项目数
    query = select(func.count()).select_from(ClipboardItem)
    result = await db.execute(query)
    total_items = result.scalar()
    
    # 最近24小时的项目数
    yesterday = datetime.utcnow() - timedelta(days=1)
    query = select(func.count()).select_from(ClipboardItem).where(
        ClipboardItem.created_at >= yesterday
    )
    result = await db.execute(query)
    recent_items = result.scalar()
    
    # 最活跃的设备
    query = select(
        ClipboardItem.device_name,
        func.count().label('count')
    ).group_by(ClipboardItem.device_name).order_by(desc('count')).limit(5)
    
    result = await db.execute(query)
    top_devices = result.all()
    
    return {
        "total_items": total_items,
        "recent_items_24h": recent_items,
        "top_devices": [
            {"device_name": device, "count": count}
            for device, count in top_devices
        ],
        "active_connections": len(manager.active_connections)
    }