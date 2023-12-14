import mimetypes
import logging
import os
from typing import Dict, Any

from .activity import BaseActivity, ActivityError
from ..types import ActivityJob, JobState
from .readers import PdfReader, FileReader


class ReadActivity(BaseActivity):
    def __init__(self, pdf_reader: PdfReader, file_reader: FileReader):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._handlers = {
            "application/pdf": pdf_reader,
            "application/json": file_reader,
            "text/plain": file_reader,
            "text/markdown": file_reader
        }

    async def perform(self, activity_job: ActivityJob, inputs: Dict[str, Any]) -> None:
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
