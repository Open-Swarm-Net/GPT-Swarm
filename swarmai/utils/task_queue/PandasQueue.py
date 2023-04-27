import uuid
import pandas as pd
from datetime import datetime

from swarmai.utils.task_queue.TaskQueueBase import TaskQueueBase
from swarmai.utils.task_queue.Task import Task
from swarmai.agents.AgentBase import AgentBase

class PandasQueue(TaskQueueBase):
    """Super simple implementatin of the versatile task queue using pandas DataFrame.
    Pretty slow, but allows for easy manipulation of tasks, filtering, etc.
    Thread-safeness is handeled by the TaskQueueBase class.

    In the current swarm architecture the taks should have following attributes:
    - task_id: unique identifier of the task
    - priority: priority of the task. Task queue will first return high priority tasks.
    - task_type: type of the task, so that specific agents can filter tasks
    - task_description: description of the task
    - status: status of the task, e.g. "pending", "in progress", "completed", "failed", 'cancelled'
    """

    def __init__(self, task_types, agent_types, task_association):
        """
        Task association is a dictionary that returns a list of task_types for a given agent_type.
        """
        super().__init__()
        self.columns = ["task_id", "priority", "task_type", "task_description", "status", "add_time", "claim_time", "complete_time", "claim_agent_id"]
        self.tasks = pd.DataFrame(columns=self.columns)
        self.task_types = task_types
        self.agent_types = agent_types
        self.task_association = task_association

    def add_task(self, task: Task) -> bool:
        """Adds a task to the queue.

        Task attr = (task_id, priority, task_type, task_description, status)
        """
        if task.task_type not in self.task_types:
            raise ValueError(f"Task type {task.task_type} is not supported.")

        if task.task_description is None:
            raise ValueError(f"Task description {task.task_description} is not valid.")

        if isinstance(task.task_description, str) == False:
            raise ValueError(f"Task description {task.task_description} is not valid.")

        if task.task_description == "":
            raise ValueError(f"Task description {task.task_description} is not valid.")
        
        priority = task.priority
        task_type = task.task_type
        task_description = task.task_description
        status = "pending"
        add_time = datetime.now()

        task_i = pd.DataFrame([[uuid.uuid4(), priority, task_type, task_description, status, add_time, None, None, None]], columns=self.columns)
        self.tasks = pd.concat([self.tasks, task_i], ignore_index=True)

    def get_task(self, agent: AgentBase) -> Task:
        """Gets the next task from the queue, based on the agent type
        """        
        supported_tasks = self._get_supported_tasks(agent.agent_type)

        df_clone = self.tasks.copy()

        # get only pending tasks
        df_clone = df_clone[df_clone["status"] == "pending"]

        # get only supported tasks
        df_clone = df_clone[df_clone["task_type"].isin(supported_tasks)]

        if len(df_clone) == 0:
            return None

        # sort by priority
        df_clone = df_clone.sort_values(by="priority", ascending=False)

        # get the first task
        task = df_clone.iloc[0]
        
        # claim the task
        status = "in progress"
        claim_time = datetime.now()
        claim_agent_id = agent.agent_id
        task_obj = Task(task_id=task["task_id"], priority=task["priority"], task_type=task["task_type"], task_description=task["task_description"], status=status)

        # update the task in the queue
        df_i = pd.DataFrame([[task["task_id"], task["priority"], task["task_type"], task["task_description"], status, task["add_time"], claim_time, None, claim_agent_id]], columns=self.columns)
        self.tasks = self.tasks[self.tasks["task_id"] != task["task_id"]]
        self.tasks = pd.concat([self.tasks, df_i], ignore_index=True)

        return task_obj

    def _get_supported_tasks(self, agent_type):
        """Returns a list of supported tasks for a given agent type.
        """
        if agent_type not in self.agent_types:
            raise ValueError(f"Agent type {agent_type} is not supported.")

        if self.task_association is None:
            # get all present task types
            return self.task_types

        return self.task_association[agent_type]
    
    def get_all_tasks(self):
        """Returns all tasks in the queue.
        Allows the manager model to bush up the tasks list to delete duplicates or unnecessary tasks.
        """
        raise NotImplementedError