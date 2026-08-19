import pytest
from memory.manager import MemoryManager


@pytest.fixture
def tmp_db(tmp_path):
    db_path = str(tmp_path / "jarvis.db")
    return MemoryManager(db_path)
