from .reader import Reader, ReaderError
import aiofiles
import yaml
import json


class YamlReader(Reader):
    async def read(self, file_path: str) -> str:
        try:
            async with aiofiles.open(file_path, mode='r') as f:
                contents = await f.read()
                yaml_data = yaml.safe_load(contents)
                json_data = json.dumps(yaml_data)
            return json_data
        except Exception as e:
            raise ReaderError(f"Failed to read text from a file: {e}")