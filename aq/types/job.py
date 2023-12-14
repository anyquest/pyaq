import uuid
from enum import Enum
from typing import Dict, Optional

from .app import App


class JobState(Enum):
    ANY = 0,
    CREATED = 1,
    RUNNING = 2,
    SUCCESS = 3
    ERROR = 4


class AppJob:
    id: str
    caller: Optional['ActivityJob']
    app: App
    context: Dict
    state: JobState

    def __init__(self, app: App):
        self.id = str(uuid.uuid4())
        self.app = app
        self.context = {}
        self.caller = None
        self.state = JobState.CREATED

    @property
    def finished(self) -> bool:
        return self.state == JobState.SUCCESS or self.state == JobState.ERROR


class ActivityJob:
    id: str
    activity_name: str
    app_job: AppJob
    state: JobState
    output: str
    output_type: str = "text/plain"

    def __init__(self, activity_name: str, app_job: AppJob):
        self.id = str(uuid.uuid4())
        self.activity_name = activity_name
        self.app_job = app_job
        self.state = JobState.CREATED
        self.output = ""

    @property
    def finished(self) -> bool:
        return self.state == JobState.SUCCESS or self.state == JobState.ERROR




