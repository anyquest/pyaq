from .reader import Reader, ReaderError
import aiofiles


class FileReader(Reader):
    async def read(self, file_path: str) -> str:
        try:
            async with aiofiles.open(file_path, mode='r') as f:
                contents = await f.read()
            return contents
        except Exception as e:
            raise ReaderError(f"Failed to read text from a file: {e}")
