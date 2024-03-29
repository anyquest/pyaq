import logging

from typing import List, Dict, Any

import yaml

from .jobs import JobManager, JobScheduler
from .types import App


class SemanticBroker:
    def __init__(self, job_manager: JobManager, job_scheduler: JobScheduler):
        self._job_manager = job_manager
        self._job_scheduler = job_scheduler
        self._logger = logging.getLogger(self.__class__.__name__)

    async def run(self, app_file: str, activity_name: str, file_path: str = None, inputs: Dict[str, Any] = None) -> Dict[str, List[str]]:
        # Load the app definition
        with open(app_file) as def_file:
            app_def = yaml.safe_load(def_file)
        app = App(**app_def)
        self._logger.info(f"Loaded {app_file}")

        # Create an activity job
        app_job = self._job_manager.create_app_job(app)
        activity_job = self._job_manager.create_activity_job(app_job, activity_name)

        # Format job inputs
        job_inputs = {"file_path": file_path} if file_path else inputs

        # Launch this job with the file as an input
        await self._job_scheduler.start_workers()
        await self._job_scheduler.schedule(activity_job, job_inputs)
        await self._job_scheduler.join()

        usage = app_job.usage
        self._logger.debug(f"prompt_tokens={usage.prompt_tokens}, completion_tokens={usage.completion_tokens}")

        return self._job_manager.get_outputs(app_job)



