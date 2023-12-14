class ReaderError(Exception):
    pass


class Reader:
    async def read(self, file_path: str) -> str:
        pass
