import os
import logging

from typing import List, Dict, Any

from ..repository import MemoryRepository
from ...types import MemoryDef

import chromadb
from chromadb.config import Settings
from ..splitter import split_into_chunks


class ChromaDbRepository(MemoryRepository):
    def __init__(self, config: Dict[str, Any]):
        self._config = config
        self._logger = logging.getLogger(self.__class__.__name__)
        logging.getLogger('chromadb').setLevel(logging.ERROR)

        path = self._config.get("path", "./data")
        if not os.path.exists(path):
            os.makedirs(path)

        self._chroma_client = chromadb.PersistentClient(path=path, settings=Settings(anonymized_telemetry=False))

    def store(self, memory_def: MemoryDef, collection: str, item_id: str, text: str, chunk_size: int) -> int:
        documents = []
        metas = []
        ids = []
        chunks = split_into_chunks(text, chunk_size)
        for i, chunk in enumerate(chunks):
            ids.append(f"{item_id} {i}")
            documents.append(chunk)
            metas.append({"item_id": item_id})

        collection = self._chroma_client.get_or_create_collection(collection)
        collection.add(ids=ids, documents=documents, metadatas=metas)
        self._logger.debug(f"Stored {len(chunks)} chunks")

        return len(ids)

    def retrieve(self, memory_def: MemoryDef, collection: str, query: str, n_results=3) -> List[str]:
        collection = self._chroma_client.get_or_create_collection(collection)
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )

        self._logger.debug(f"Retrieved {len(results['distances'][0])} chunks")
        for distance in results["distances"][0]:
            self._logger.debug(f"distance: {distance}")

        return results["documents"][0]
