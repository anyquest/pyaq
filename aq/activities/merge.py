import logging
from typing import Dict, Any

import markdown
import yaml
import json

from .activity import BaseActivity
from ..types import ActivityJob, JobState


class MergeActivity(BaseActivity):
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
            template = activity.parameters.get("template", "")
            if template:
                text = self.render(template, inputs)
                output_type = "text/markdown"
            elif output_format == "json":
                text = self.merge_inputs_json(inputs, indent=2)
                output_type = "application/json"
            elif output_format == "yaml":
                text = self.merge_inputs_json(inputs)
                text = yaml.dump(json.loads(text), default_flow_style=False)
                output_type = "text/yaml"
            else:
                text = self.merge_inputs(inputs)
                output_type = "text/markdown"

            # Apply formatting
            if output_format == "html":
                text = self.HTML_TEMPLATE % markdown.markdown(text, tab_length=2)
                output_type = "text/html"

            activity_job.state = JobState.SUCCESS
            activity_job.output_type = output_type
            activity_job.output = text

        except Exception as e:
            self._logger.error(e)
            activity_job.state = JobState.ERROR
            activity_job.output = str(e)




