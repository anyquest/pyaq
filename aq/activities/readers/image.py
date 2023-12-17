from .reader import Reader, ReaderError
import aiofiles
import base64
import mimetypes


class ImageReader(Reader):
    async def read(self, file_path: str) -> str:
        try:
            content_type = mimetypes.guess_type(file_path)[0]
            async with aiofiles.open(file_path, mode='rb') as f:
                contents = await f.read()
            encoded_contents = base64.b64encode(contents).decode()
            return f"data:{content_type};base64,{encoded_contents}"
        except Exception as e:
            raise ReaderError(f"Failed to read text from a file: {e}")
