from .reader import Reader, ReaderError
import pypdf


class PdfReader(Reader):
    async def read(self, file_path: str) -> str:
        try:
            reader = pypdf.PdfReader(file_path)
            text = [page.extract_text() for page in reader.pages]
            return "\n\n".join(text)
        except Exception as e:
            raise ReaderError(f"Failed to read text from PDF: {e}")
