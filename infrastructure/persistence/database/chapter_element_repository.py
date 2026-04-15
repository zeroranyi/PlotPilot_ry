"""
章节元素关联 Repository
"""

import sqlite3
from typing import List, Optional
from datetime import datetime

from domain.structure.chapter_element import ChapterElement, ElementType, RelationType, Importance


class ChapterElementRepository:
    """章节元素关联仓储"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def save(self, element: ChapterElement) -> ChapterElement:
        """保存章节元素关联"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chapter_elements (
                    id, chapter_id, element_type, element_id,
                    relation_type, importance, appearance_order, notes,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                element.id,
                element.chapter_id,
                element.element_type.value,
                element.element_id,
                element.relation_type.value,
                element.importance.value,
                element.appearance_order,
                element.notes,
                element.created_at.isoformat(),
            ))
            conn.commit()
            return element
        finally:
            conn.close()

    async def save_batch(self, elements: List[ChapterElement]) -> List[ChapterElement]:
        """批量保存章节元素关联"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            for element in elements:
                cursor.execute("""
                    INSERT OR REPLACE INTO chapter_elements (
                        id, chapter_id, element_type, element_id,
                        relation_type, importance, appearance_order, notes,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    element.id,
                    element.chapter_id,
                    element.element_type.value,
                    element.element_id,
                    element.relation_type.value,
                    element.importance.value,
                    element.appearance_order,
                    element.notes,
                    element.created_at.isoformat(),
                ))
            conn.commit()
            return elements
        finally:
            conn.close()

    async def get_by_chapter(self, chapter_id: str) -> List[ChapterElement]:
        """获取章节的所有元素关联"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM chapter_elements
                WHERE chapter_id = ?
                ORDER BY appearance_order, created_at
            """, (chapter_id,))
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
        finally:
            conn.close()

    async def get_by_element(
        self,
        element_type: ElementType,
        element_id: str
    ) -> List[ChapterElement]:
        """获取某个元素在哪些章节出现"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM chapter_elements
                WHERE element_type = ? AND element_id = ?
                ORDER BY created_at
            """, (element_type.value, element_id))
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
        finally:
            conn.close()

    async def get_by_chapter_and_type(
        self,
        chapter_id: str,
        element_type: ElementType
    ) -> List[ChapterElement]:
        """获取章节中某类型的所有元素"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM chapter_elements
                WHERE chapter_id = ? AND element_type = ?
                ORDER BY appearance_order, created_at
            """, (chapter_id, element_type.value))
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
        finally:
            conn.close()

    async def delete(self, element_id: str) -> bool:
        """删除章节元素关联"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chapter_elements WHERE id = ?", (element_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    async def delete_by_chapter(self, chapter_id: str) -> int:
        """删除章节的所有元素关联"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chapter_elements WHERE chapter_id = ?", (chapter_id,))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    async def exists(
        self,
        chapter_id: str,
        element_type: ElementType,
        element_id: str,
        relation_type: RelationType
    ) -> bool:
        """检查关联是否已存在"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM chapter_elements
                WHERE chapter_id = ? AND element_type = ?
                AND element_id = ? AND relation_type = ?
            """, (chapter_id, element_type.value, element_id, relation_type.value))
            count = cursor.fetchone()[0]
            return count > 0
        finally:
            conn.close()

    def _row_to_entity(self, row: sqlite3.Row) -> ChapterElement:
        """将数据库行转换为实体"""
        return ChapterElement(
            id=row["id"],
            chapter_id=row["chapter_id"],
            element_type=ElementType(row["element_type"]),
            element_id=row["element_id"],
            relation_type=RelationType(row["relation_type"]),
            importance=Importance(row["importance"]),
            appearance_order=row["appearance_order"],
            notes=row["notes"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
