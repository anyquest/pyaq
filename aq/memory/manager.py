import logging

from .repository import MemoryRepository
from .chromadb import ChromaDbRepository
from ..types import MemoryType


class MemoryManager:
    def __init__(self, chromadb_repository: ChromaDbRepository):
        self._repositories = {
            MemoryType.CHROMADB: chromadb_repository
        }
        self._logger = logging.getLogger(self.__class__.__name__)

    def get_repository(self, memory_type: MemoryType) -> MemoryRepository:
        return self._repositories[memory_type]
