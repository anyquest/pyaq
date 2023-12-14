import logging
from typing import Dict, Any

from .activity import BaseActivity, ActivityError
from ..types import ActivityJob, JobState
from ..memory import MemoryManager


class RetrieveActivity(BaseActivity):
    def __init__(self, memory_manager: MemoryManager):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._memory_manager = memory_manager

    async def perform(self, activity_job: ActivityJob, inputs: Dict[str, Any]) -> None:
        try:
            app = activity_job.app_job.app
            if not app.memory:
                raise ActivityError("A memory repository is required for this app")

            activity = app.activities[activity_job.activity_name]
            if not activity.memory:
                raise ActivityError("A memory repository is required for this activity")

            memory_def = app.memory[activity.memory[0]]
            memory_repository = self._memory_manager.get_repository(memory_def.type)

            n_results = activity.parameters.get("n_results", 3)

            chunks = memory_repository.retrieve(memory_def, app.info.id, self.merge_inputs(inputs), n_results)

            activity_job.state = JobState.SUCCESS
            activity_job.output = "\n\n".join(chunks)
            activity_job.output_type = "text/plain"

        except Exception as e:
            activity_job.state = JobState.ERROR
            activity_job.output = str(e)
            self._logger.error(f"Encountered an error {e}")
