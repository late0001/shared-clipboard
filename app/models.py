from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class ClipboardItem(Base):
    """剪贴板项目模型"""
    __tablename__ = "clipboard_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text")  # text, image, file
    device_name = Column(String(100))
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "content_type": self.content_type,
            "device_name": self.device_name,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class ClipboardHistory(Base):
    """剪贴板历史记录"""
    __tablename__ = "clipboard_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)