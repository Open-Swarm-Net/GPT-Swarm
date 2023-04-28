import os
import openai
import re

from swarmai.agents.AgentBase import AgentBase
from swarmai.utils.ai_engines.GPTConversEngine import GPTConversEngine
from swarmai.utils.task_queue.Task import Task
from swarmai.utils.memory.DictInternalMemory import DictInternalMemory
from swarmai.utils.PromptFactory import PromptFactory

class GeneralPurposeAgent(AgentBase):
    """Manager agent class that is responsible for breaking down the tasks into subtasks and assigning them into the task queue.

    Attributes:
        - 
    """

    def __init__(self, agent_id, agent_type, swarm, logger):
        super().__init__(agent_id, agent_type, swarm, logger)
        self.engine = GPTConversEngine("gpt-3.5-turbo", 0.5, 1000)
        
        self.TASK_METHODS = {}
        for method in self.swarm.TASK_TYPES:
            if method != "breakdown_to_subtasks":
                self.TASK_METHODS[method] = self._think

    def perform_task(self):
        self.step = "perform_task"
        try:
            # self.task is already taken in the beginning of the cycle in AgentBase
            if not isinstance(self.task, Task):
                raise Exception(f"Task is not of type Task, but {type(self.task)}")
            
            task_type = self.task.task_type
            if task_type not in self.TASK_METHODS:
                raise Exception(f"Task type {task_type} is not supported by the agent {self.agent_id} of type {self.agent_type}")
            
            self.result = self.TASK_METHODS[task_type](self.task.task_description)
            return True
        except Exception as e:
            self.log(messag = f"Agent {self.agent_id} of type {self.agent_type} failed to perform the task {self.task.task_description} with error {e}", level = "error")
            return False

    def share(self):
        pass

    def _think(self, task_description):
        self.step = "think"
        prompt = f"You need to perform a task: {task_description}. The type of the task is {self.task.task_type}. If you don't have capabilities to perform the task (for example no google access), image you do have them and submit the imagined solution."

        # generate a conversation
        conversation = [
            {"role": "user", "content": prompt}
        ]

        result = self.engine.call_model(conversation)

        # add to shared memory
        self.shared_memory.add_entry(
            score = 1,
            agent_id = self.agent_id,
            agent_cycle = self.cycle,
            entry = result
        )
