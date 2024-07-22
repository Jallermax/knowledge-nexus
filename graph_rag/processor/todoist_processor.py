import logging

from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task

from graph_rag.config.config_manager import Config

logger = logging.getLogger(__name__)

class TodoistProcessor:
    def __init__(self):
        self.config = Config()
        self.todoist_api = TodoistAPI(token=self.config.TODOIST_API_KEY)

        logger.info("TodoistProcessor initialized")

    def get_all_tasks(self, sync_completed=False):
        return self.todoist_api.get_tasks()

    def get_all_labels(self):
        return self.todoist_api.get_labels()

    def get_all_projects(self):
        return self.todoist_api.get_projects()

    def get_task(self, task_id: str) -> Task | None:
        try:
            return self.todoist_api.get_task(task_id)
        except Exception as e:
            logger.error(f"Task with id {task_id} not found: {e}")
            return None
