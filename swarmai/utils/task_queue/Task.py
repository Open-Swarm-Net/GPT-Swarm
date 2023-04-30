import uuid

class Task:
    """A simple representation of a task that is used ONLY for exchage between agents and task queues.
    Is purely a data structure, so no methods are needed. Thread-safeness must be handled in the task queue, not here.

    Attributes:
    - task_id: unique identifier of the task
    - priority: priority of the task. Task queue will first return high priority tasks.
    - task_type: type of the task, so that specific agents can filter tasks
    - task_description: description of the task
    - status: status of the task, e.g. "pending", "in progress", "completed", "failed", 'cancelled'
    """

    class TaskTypes:
        """Task types that are supported by the task queue
        """
        google_search = "google_search"
        breakdown_to_subtasks = "breakdown_to_subtasks"
        summarisation = "summarisation"
        analysis = "analysis"
        report_preparation = "report_preparation"
        crunchbase_search = "crunchbase_search"

    def __init__(self, priority, task_type, task_description, status="pending", task_id=uuid.uuid4()):
        self.task_id = task_id
        self.priority = priority
        self.task_type = task_type
        self.task_description = task_description
        self.status = status

    def __str__(self):
        return f"task_id: {self.task_id}\npriority: {self.priority}\ntask_type: {self.task_type}\ntask_description: {self.task_description}\nstatus: {self.status}"
    
    def __repr__(self):
        return self.__str__(self)
