"""
KIRA — People Memory
Remember people: names, relations, details
"""

import json
import time
from pathlib import Path
from sqlalchemy import Column, Integer, String, Text, Float
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.ext.declarative import declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/kira_memory.db")
Base = declarative_base()


class PersonModel(Base):
    __tablename__ = "people"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    relation = Column(String(100))
    details = Column(Text)
    photo_path = Column(String(500), nullable=True)
    added_at = Column(Float, default=time.time)
    updated_at = Column(Float, default=time.time)


class PeopleMemory:
    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.cache = {}

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await self._load_cache()

    async def _load_cache(self):
        """Load all people to cache"""
        async with AsyncSession(self.engine) as session:
            result = await session.execute(select(PersonModel))
            people = result.scalars().all()
            for p in people:
                self.cache[p.name.lower()] = {
                    "name": p.name,
                    "relation": p.relation,
                    "details": json.loads(p.details) if p.details else {},
                    "photo_path": p.photo_path
                }

    async def add_person(self, name: str, relation: str = "", details: dict = {}) -> str:
        """Add or update a person"""
        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                select(PersonModel).where(PersonModel.name == name)
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.relation = relation or existing.relation
                existing.updated_at = time.time()
                if details:
                    old = json.loads(existing.details) if existing.details else {}
                    old.update(details)
                    existing.details = json.dumps(old)
            else:
                person = PersonModel(
                    name=name,
                    relation=relation,
                    details=json.dumps(details),
                )
                session.add(person)

            await session.commit()

        # Update cache
        self.cache[name.lower()] = {
            "name": name,
            "relation": relation,
            "details": details,
            "photo_path": None
        }
        return f"{name} yaad kar liya"

    async def get_person(self, name: str) -> dict | None:
        """Get person details"""
        return self.cache.get(name.lower())

    async def search_person(self, query: str) -> list:
        """Search people by name or relation"""
        results = []
        query_lower = query.lower()
        for key, person in self.cache.items():
            if (query_lower in key or
                query_lower in person.get("relation", "").lower() or
                query_lower in str(person.get("details", "")).lower()):
                results.append(person)
        return results

    async def add_photo_to_person(self, name: str, photo_path: str) -> str:
        """Link photo to person"""
        if name.lower() in self.cache:
            self.cache[name.lower()]["photo_path"] = photo_path
            async with AsyncSession(self.engine) as session:
                result = await session.execute(
                    select(PersonModel).where(PersonModel.name == name)
                )
                person = result.scalar_one_or_none()
                if person:
                    person.photo_path = photo_path
                    await session.commit()
            return f"{name} ki photo save ho gayi"
        return f"{name} nahi mila, pehle add karo"

    async def list_all(self) -> list:
        """List all people"""
        return list(self.cache.values())

    def format_person_info(self, person: dict) -> str:
        """Format person info for response"""
        if not person:
            return "Ye insaan yaad nahi"

        info = f"{person['name']}"
        if person.get('relation'):
            info += f" — {person['relation']}"
        if person.get('details'):
            for k, v in person['details'].items():
                info += f", {k}: {v}"
        return info


# Singleton
people_memory = PeopleMemory()
