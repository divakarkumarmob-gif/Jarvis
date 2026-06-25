"""
KIRA — Conversation Memory
Permanent conversation storage with SQLite
"""

import os
import json
import time
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/kira_memory.db")

Path("data").mkdir(exist_ok=True)

Base = declarative_base()


class ConversationModel(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100))
    role = Column(String(20))
    content = Column(Text)
    timestamp = Column(Float, default=time.time)
    mode = Column(String(50), default="normal")


class ConversationMemory:
    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.session_id = f"session_{int(time.time())}"
        self.recent_cache = []
        self.max_cache = 20

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def save_message(self, role: str, content: str, mode: str = "normal"):
        """Save message to DB"""
        if mode == "privacy":
            return

        async with AsyncSession(self.engine) as session:
            msg = ConversationModel(
                session_id=self.session_id,
                role=role,
                content=content,
                timestamp=time.time(),
                mode=mode
            )
            session.add(msg)
            await session.commit()

        # Update cache
        self.recent_cache.append({"role": role, "content": content})
        if len(self.recent_cache) > self.max_cache:
            self.recent_cache = self.recent_cache[-self.max_cache:]

    async def get_recent(self, limit: int = 20) -> list:
        """Get recent conversation"""
        return self.recent_cache[-limit:]

    async def search_memory(self, query: str) -> list:
        """Search conversation history"""
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(ConversationModel).where(
                    ConversationModel.content.contains(query)
                ).order_by(ConversationModel.timestamp.desc()).limit(10)
            )
            rows = result.scalars().all()
            return [{"role": r.role, "content": r.content, "time": r.timestamp} for r in rows]

    async def clear_session(self):
        """Clear current session cache"""
        self.recent_cache = []
        self.session_id = f"session_{int(time.time())}"

    async def get_summary(self) -> str:
        """Get conversation summary for context"""
        if not self.recent_cache:
            return ""
        recent = self.recent_cache[-10:]
        return "\n".join([f"{m['role']}: {m['content']}" for m in recent])


# Singleton
conversation_memory = ConversationMemory()
