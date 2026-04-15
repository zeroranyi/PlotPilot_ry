"""
章节场景 Repository
"""

import sqlite3
import json
from typing import List, Optional
from datetime import datetime

from domain.structure.chapter_scene import ChapterScene


class ChapterSceneRepository:
    """章节场景仓储"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def save(self, scene: ChapterScene) -> ChapterScene:
        """保存章节场景"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chapter_scenes (
                    id, chapter_id, scene_number, order_index,
                    location_id, timeline, summary, purpose,
                    content, word_count, characters,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scene.id,
                scene.chapter_id,
                scene.scene_number,
                scene.order_index,
                scene.location_id,
                scene.timeline,
                scene.summary,
                scene.purpose,
                scene.content,
                scene.word_count,
                json.dumps(scene.characters),
                scene.created_at.isoformat(),
                scene.updated_at.isoformat(),
            ))
            conn.commit()
            return scene
        finally:
            conn.close()

    async def update(self, scene: ChapterScene) -> ChapterScene:
        """更新章节场景"""
        scene.updated_at = datetime.now()
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE chapter_scenes SET
                    scene_number = ?,
                    order_index = ?,
                    location_id = ?,
                    timeline = ?,
                    summary = ?,
                    purpose = ?,
                    content = ?,
                    word_count = ?,
                    characters = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                scene.scene_number,
                scene.order_index,
                scene.location_id,
                scene.timeline,
                scene.summary,
                scene.purpose,
                scene.content,
                scene.word_count,
                json.dumps(scene.characters),
                scene.updated_at.isoformat(),
                scene.id,
            ))
            conn.commit()
            return scene
        finally:
            conn.close()

    async def save_batch(self, scenes: List[ChapterScene]) -> List[ChapterScene]:
        """批量保存章节场景"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            for scene in scenes:
                cursor.execute("""
                    INSERT OR REPLACE INTO chapter_scenes (
                        id, chapter_id, scene_number, order_index,
                        location_id, timeline, summary, purpose,
                        content, word_count, characters,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    scene.id,
                    scene.chapter_id,
                    scene.scene_number,
                    scene.order_index,
                    scene.location_id,
                    scene.timeline,
                    scene.summary,
                    scene.purpose,
                    scene.content,
                    scene.word_count,
                    json.dumps(scene.characters),
                    scene.created_at.isoformat(),
                    scene.updated_at.isoformat(),
                ))
            conn.commit()
            return scenes
        finally:
            conn.close()

    async def get_by_id(self, scene_id: str) -> Optional[ChapterScene]:
        """根据 ID 获取场景"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chapter_scenes WHERE id = ?", (scene_id,))
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
        finally:
            conn.close()

    async def get_by_chapter(self, chapter_id: str) -> List[ChapterScene]:
        """获取章节的所有场景"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM chapter_scenes
                WHERE chapter_id = ?
                ORDER BY order_index, scene_number
            """, (chapter_id,))
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
        finally:
            conn.close()

    async def delete(self, scene_id: str) -> bool:
        """删除场景"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chapter_scenes WHERE id = ?", (scene_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    async def delete_by_chapter(self, chapter_id: str) -> int:
        """删除章节的所有场景"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chapter_scenes WHERE chapter_id = ?", (chapter_id,))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def _row_to_entity(self, row: sqlite3.Row) -> ChapterScene:
        """将数据库行转换为实体"""
        return ChapterScene(
            id=row["id"],
            chapter_id=row["chapter_id"],
            scene_number=row["scene_number"],
            order_index=row["order_index"],
            location_id=row["location_id"],
            timeline=row["timeline"],
            summary=row["summary"],
            purpose=row["purpose"],
            content=row["content"],
            word_count=row["word_count"],
            characters=json.loads(row["characters"]) if row["characters"] else [],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
