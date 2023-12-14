import asyncio
import logging
import time
from typing import Dict, Any

from .manager import JobManager, AppJobError
from ..activities import (
    ReadActivity,
    WriteActivity,
    SummarizeActivity,
    GenerateActivity,
    ExtractActivity,
    StoreActivity,
    RetrieveActivity,
    FunctionActivity,
    ReturnActivity
)
from ..types import ActivityType, ActivityJob, JobState


class WorkItem:
    job: ActivityJob
    inputs: Dict[str, Any]

    def __init__(self, job: ActivityJob, inputs: Dict[str, Any]) -> None:
        self.job = job
        self.inputs = inputs


class JobScheduler:
    def __init__(self, config: Dict[str, Any], job_manager: JobManager,
                 read_activity: ReadActivity, write_activity: WriteActivity,
                 summarize_activity: SummarizeActivity, generate_activity: GenerateActivity,
                 extract_activity: ExtractActivity, store_activity: StoreActivity, retrieve_activity: RetrieveActivity,
                 function_activity: FunctionActivity, return_activity: ReturnActivity):
        self._config = config

        self._logger = logging.getLogger(self.__class__.__name__)
        logging.getLogger('asyncio').setLevel(logging.ERROR)

        self._queue = asyncio.Queue()
        self._workers = []
        self._job_manager = job_manager

        self._activity_handlers = {
            ActivityType.READ: read_activity,
            ActivityType.WRITE: write_activity,
            ActivityType.SUMMARIZE: summarize_activity,
            ActivityType.GENERATE: generate_activity,
            ActivityType.EXTRACT: extract_activity,
            ActivityType.STORE: store_activity,
            ActivityType.RETRIEVE: retrieve_activity,
            ActivityType.FUNCTION: function_activity,
            ActivityType.RETURN: return_activity
        }

    async def start_workers(self):
        num_workers = self._config.get("workers", 3)
        self._workers = [asyncio.create_task(self.consume(n)) for n in range(num_workers)]

    async def schedule(self, activity_job: ActivityJob, inputs: Dict[str, Any]) -> None:
        item = WorkItem(activity_job, inputs)
        await self._queue.put(item)

    async def consume(self, name: int) -> None:
        while True:
            item = await self._queue.get()
            self._logger.debug(f"Worker {name} performing {item.job.activity_name}")
            start_time = time.perf_counter()
            await self.perform(item)
            self._logger.debug(f"Finished {item.job.activity_name} in {int(time.perf_counter()-start_time)} sec.")
            self._queue.task_done()

    async def perform(self, item: WorkItem) -> None:
        item.job.state = JobState.RUNNING
        app = item.job.app_job.app
        app_job = item.job.app_job

        activity = app.activities[item.job.activity_name]
        activity_type = activity.type

        if activity_type == ActivityType.CALL:
            # Push a new app job on the call stack
            function_name = activity.parameters["function"]
            if function_name and function_name in app.activities:
                app_job = self._job_manager.create_app_job(app)
                app_job.caller = item.job
                function_job = self._job_manager.create_activity_job(app_job, function_name)
                await self.schedule(function_job, item.inputs)
            else:
                raise AppJobError(f"The function name in a call activity is incorrect or missing")
        else:
            handler = self._activity_handlers.get(activity_type)
            if handler:
                await handler.perform(item.job, item.inputs)
                if item.job.state == JobState.SUCCESS:
                    # Pop the app job stack if it's a return activity
                    if activity_type == ActivityType.RETURN and app_job.caller:
                        # Update the state of the caller activity
                        activity_job = app_job.caller
                        activity_job.state = JobState.SUCCESS
                        activity_job.output = item.job.output
                        activity_job.output_type = item.job.output_type

                        # Update the state of the callee app job
                        app_job.state = JobState.SUCCESS
                        app_job = activity_job.app_job
                    else:
                        activity_job = item.job

                    # Schedule next jobs
                    next_activities = self._job_manager.get_next_activities(activity_job)
                    for next_activity in next_activities:
                        all_inputs = self._job_manager.get_inputs_for_activity(app_job, app.activities[next_activity])
                        for job_inputs in all_inputs:
                            next_job = self._job_manager.create_activity_job(app_job, next_activity)
                            await self.schedule(next_job, job_inputs)
                else:
                    self._logger.error(f"{item.job.activity_name} failed with error {item.job.output}")
            else:
                raise AppJobError(f"Unknown activity type {activity_type}")

    async def join(self) -> None:
        await self._queue.join()
        for w in self._workers:
            w.cancel()
        self._logger.debug("Finished work items")
