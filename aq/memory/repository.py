from typing import List
from ..types import MemoryDef


class MemoryRepository:
    def store(self, memory_def: MemoryDef, collection: str, item_id: str, text: str, chunk_size: int) -> int:
        return 0

    def retrieve(self, memory_def: MemoryDef, collection: str, query: str, n_results=3) -> List[str]:
        return []

