import logging
from typing import Dict, Any

from .activity import BaseActivity
from ..types import ActivityJob, JobState


class FunctionActivity(BaseActivity):
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    async def perform(self, activity_job: ActivityJob, inputs: Dict[str, Any]) -> None:
        activity_job.state = JobState.SUCCESS
        activity_job.output = self.merge_inputs(inputs)
        activity_job.output_type = "text/plain"


class ReturnActivity(BaseActivity):
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    async def perform(self, activity_job: ActivityJob, inputs: Dict[str, Any]) -> None:
        try:
            activity_job.state = JobState.SUCCESS
            activity_job.output = self.merge_inputs_json(inputs)
            activity_job.output_type = "application/json"
        except Exception as e:
            activity_job.state = JobState.ERROR
            activity_job.output = str(e)
            self._logger.error(f"Encountered an error {e}")

