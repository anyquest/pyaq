import logging
import uuid
from typing import Dict, Any

from .activity import BaseActivity, ActivityError
from ..types import ActivityJob, JobState
from ..memory import MemoryManager


class StoreActivity(BaseActivity):
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

            file_id = activity_job.app_job.context.get("file_path", str(uuid.uuid4()))
            chunk_size = activity.parameters.get("chunk_size", memory_def.parameters.get("chunk_size", 2000))

            text = self.merge_inputs(inputs)
            chunks = memory_repository.store(memory_def, app.info.id, file_id, text, chunk_size)

            activity_job.state = JobState.SUCCESS
            activity_job.output = str(chunks)
            activity_job.output_type = "text/plain"

        except Exception as e:
            activity_job.state = JobState.ERROR
            activity_job.output = str(e)
            self._logger.error(f"Encountered an error {e}")
