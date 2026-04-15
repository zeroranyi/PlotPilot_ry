"""仓库内路径（不依赖进程当前工作目录）。"""
from pathlib import Path

# application/paths.py → 仓库根目录 aitext/
AITEXT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = AITEXT_ROOT / "data"


def get_db_path() -> str:
    """获取数据库文件路径

    Returns:
        数据库文件的绝对路径字符串
    """
    return str(DATA_DIR / "aitext.db")
