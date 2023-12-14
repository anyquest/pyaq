import json
import logging
from typing import Dict, List, Any

from jsonpath_ng import parse

from ..types import App, Activity, AppJob, ActivityJob


class AppJobError(Exception):
    pass


class JobManager:
    app_jobs: Dict[str, AppJob]
    activity_jobs: Dict[str, Dict[str, List[ActivityJob]]]

    def __init__(self):
        self.app_jobs = {}
        self.activity_jobs = {}
        self._logger = logging.getLogger(self.__class__.__name__)

    def create_app_job(self, app: App) -> AppJob:
        app_job = AppJob(app)
        self.app_jobs[app_job.id] = app_job
        self.activity_jobs[app_job.id] = {}
        return app_job

    def create_activity_job(self, app_job: AppJob, activity_name: str) -> ActivityJob:
        app = app_job.app
        if activity_name not in app.activities:
            raise AppJobError(f"Activity {activity_name} not found")
        activity_job = ActivityJob(activity_name, app_job)
        self.activity_jobs[app_job.id].setdefault(activity_name, []).append(activity_job)
        return activity_job

    def get_next_activities(self, activity_job: ActivityJob) -> List[str]:
        app = activity_job.app_job.app
        rv = []
        for activity_name in app.activities:
            activity = app.activities[activity_name]
            for activity_input in activity.inputs or []:
                if (activity_input.activity == activity_job.activity_name and
                        not self.is_waiting_for_jobs(activity_job.app_job, activity)):
                    rv.append(activity_name)
        return rv

    def is_waiting_for_jobs(self, app_job: AppJob, activity: Activity):
        for activity_input in activity.inputs or []:
            jobs = self.activity_jobs[app_job.id].get(activity_input.activity, None)
            if not jobs or any(not job.finished for job in jobs):
                return True
        return False

    def get_inputs_for_activity(self, app_job: AppJob, activity: Activity) -> List[Dict[str, Any]]:
        inputs_for_activity = {}
        if activity.inputs:
            for activity_input in activity.inputs:
                job_outputs = [job.output for job in self.activity_jobs[app_job.id].get(activity_input.activity, [])]
                inputs_for_activity[activity_input.activity] = job_outputs if len(job_outputs) > 1 else job_outputs[0]

            for activity_input in activity.inputs:
                if activity_input.map:
                    try:
                        expr = parse(activity_input.map)
                        val = inputs_for_activity[activity_input.activity]
                        inputs = []
                        for match in expr.find(json.loads(val)):
                            if isinstance(match.value, list):
                                for input_value in match.value:
                                    inputs.append({**inputs_for_activity, activity_input.activity: input_value})
                        return inputs
                    except Exception as e:
                        self._logger.error(f"Failed to parse a map expression {e}")
                        return []

        return [inputs_for_activity]

    def get_outputs(self, app_job: AppJob) -> Dict[str, Any]:
        app = app_job.app

        # Terminal activities have inputs and do not have any other activities that take their outputs
        terminal_activities = [
            activity_name
            for activity_name, activity in app.activities.items()
            if activity.inputs and not any(
                activity_input.activity == activity_name
                for some_other_activity in app.activities.values()
                for activity_input in some_other_activity.inputs or []
            )
        ]

        # Collect outputs from terminal activities
        outputs = {
            activity_name: [job.output for job in self.activity_jobs[app_job.id].get(activity_name, [])]
            for activity_name in terminal_activities
        }

        # Remove empty values and return
        return {key: value for key, value in outputs.items() if value}
