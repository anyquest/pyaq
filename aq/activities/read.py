import logging
import mimetypes
import os
from typing import Dict

from ..types import ActivityJob, JobState
from .activity import ActivityError, BaseActivity
from .readers import FileReader, ImageReader, PdfReader, YamlReader


class ReadActivity(BaseActivity):
    def __init__(self, pdf_reader: PdfReader, file_reader: FileReader, image_reader: ImageReader, yaml_reader: YamlReader):
        self._logger = logging.getLogger(self.__class__.__name__)

        mimetypes.add_type("text/yaml", ".yaml")        
        mimetypes.add_type("text/yaml", ".yml")        
        mimetypes.add_type("text/markdown", ".md")        

        self._handlers = {
            "application/pdf": pdf_reader,
            "application/json": file_reader,
            "text/yaml": yaml_reader,
            "text/plain": file_reader,
            "text/markdown": file_reader,
            "image/jpeg": image_reader,
            "image/jpg": image_reader,
            "image/png": image_reader
        }

    async def perform(self, activity_job: ActivityJob, inputs: Dict[str, str]) -> None:
        try:
            file_path = inputs.get("file_path")
            if not file_path or not os.path.exists(file_path):
                raise ActivityError(f"Invalid file path: {file_path}")

            content_type = mimetypes.guess_type(file_path)[0]
            handler = self._handlers.get(content_type)
            if handler:
                content = await handler.read(file_path)
            else:
                raise ActivityError(f"Cannot read content of type: {content_type}")

            # Add the file path to the app context
            app_job = activity_job.app_job
            app_job.context["file_path"] = file_path

            activity_job.state = JobState.SUCCESS
            activity_job.output = content
            activity_job.output_type = "text/plain"

        except Exception as e:
            activity_job.state = JobState.ERROR
            activity_job.output = str(e)
            self._logger.error(f"Encountered an error {e}")
