import logging
import os
from typing import Dict, Any

import aiofiles
import markdown

from .activity import BaseActivity
from ..types import ActivityJob, JobState


class WriteActivity(BaseActivity):
    HTML_TEMPLATE = """<html>
<head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <style>
        .content {
            width: 80%%;
            margin: auto;
            line-height: 1.4rem;
            font-family: Helvetica, Arial, sans-serif;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="content">
        %s
    </div>
</body>
</html>"""

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    async def perform(self, activity_job: ActivityJob, inputs: Dict[str, Any]) -> None:
        try:
            app = activity_job.app_job.app
            activity = app.activities[activity_job.activity_name]

            # Collate the inputs
            output_format = activity.parameters.get("format", "md")
            template = activity.parameters.get("template", None)
            if template:
                text = self.render(template, inputs)
            elif output_format == "json":
                text = self.merge_inputs_json(inputs, indent=2)
            else:
                text = self.merge_inputs(inputs)

            # Apply formatting
            if output_format == "html":
                text = self.HTML_TEMPLATE % markdown.markdown(text, tab_length=2)

            # Write content to file
            file_name = activity.parameters.get("filename") or os.path.splitext(os.path.basename(activity_job.app_job.context.get("file_path", "")))[0] or "out"
            file_path = os.path.join("./out", file_name)

            async with aiofiles.open(file_path, mode='w', encoding='utf-8') as file:
                await file.write(text)

            activity_job.state = JobState.SUCCESS
            activity_job.output = file_path

        except Exception as e:
            self._logger.error(e)
            activity_job.state = JobState.ERROR
            activity_job.output = str(e)




