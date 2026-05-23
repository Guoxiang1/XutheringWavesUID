from __future__ import annotations

import json
import asyncio
from pathlib import Path
from typing import Dict, Optional


class BindStore:
    """AstrBot 基础版 UID 绑定存储。"""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def _load(self) -> Dict[str, Dict[str, str]]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text("utf-8"))
        except Exception:
            return {}

    async def _save(self, data: Dict[str, Dict[str, str]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

    async def bind(self, user_id: str, uid: str) -> None:
        async with self._lock:
            data = await self._load()
            data[str(user_id)] = {"uid": str(uid)}
            await self._save(data)

    async def get(self, user_id: str) -> Optional[str]:
        async with self._lock:
            data = await self._load()
            row = data.get(str(user_id)) or {}
            uid = row.get("uid")
            return str(uid) if uid else None

    async def delete(self, user_id: str) -> bool:
        async with self._lock:
            data = await self._load()
            existed = str(user_id) in data
            data.pop(str(user_id), None)
            await self._save(data)
            return existed
