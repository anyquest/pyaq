import logging
import os
from typing import Dict, Any

import aiofiles

from .merge import MergeActivity
from ..types import ActivityJob, JobState


class WriteActivity(MergeActivity):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)

    async def perform(self, activity_job: ActivityJob, inputs: Dict[str, Any]) -> None:
        try:
            app = activity_job.app_job.app
            activity = app.activities[activity_job.activity_name]

            await super().perform(activity_job, inputs)

            # Compute the file prefix based on the original file name
            original_file_path = activity_job.app_job.context.get("file_path", "")
            if original_file_path:
                base_name = os.path.basename(original_file_path)
                file_prefix, _ = os.path.splitext(base_name)
            else:
                file_prefix = "out"

            if activity_job.output_type == "application/json":
                ext = "json"
            elif activity_job.output_type == "text/markdown":
                ext = "md"
            elif activity_job.output_type == "text/html":
                ext = "html"
            elif activity_job.output_type == "text/plain":
                ext = "txt"
            elif activity_job.output_type == "text/yaml":
                ext = "yml"
            else:
                ext = "out"

            # Write content to file
            file_name = activity.parameters.get("filename", self.generate_temp_filename(file_prefix, ext))

            # Create the out directory
            path = "./out"
            if not os.path.exists(path):
                os.makedirs(path)

            file_path = os.path.join(path, file_name)
            async with aiofiles.open(file_path, mode='w', encoding='utf-8') as file:
                await file.write(activity_job.output)

            activity_job.state = JobState.SUCCESS
            activity_job.output = file_path

        except Exception as e:
            self._logger.error(e)
            activity_job.state = JobState.ERROR
            activity_job.output = str(e)




