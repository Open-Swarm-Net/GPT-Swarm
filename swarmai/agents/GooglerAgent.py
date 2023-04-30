from swarmai.agents.AgentBase import AgentBase
from swarmai.utils.ai_engines import LanchainGoogleEngine, GPTConversEngine
from swarmai.utils.task_queue.Task import Task
from swarmai.utils.PromptFactory import PromptFactory

class GooglerAgent(AgentBase):
    """Googler agent that can google things.
    """

    def __init__(self, agent_id, agent_type, swarm, logger):
        super().__init__(agent_id, agent_type, swarm, logger)
        self.search_engine = LanchainGoogleEngine("gpt-3.5-turbo", 0.5, 1000)
        self.thinking_engine = GPTConversEngine("gpt-3.5-turbo", 0.5, 1000)
        
        self.TASK_METHODS = {
            Task.TaskTypes.google_search: self.google,
        }

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
            self.log(message = f"Agent {self.agent_id} of type {self.agent_type} failed to perform the task {self.task.task_description} with error {e}", level = "error")
            return False
        
    def share(self):
        pass

    def google(self, task_description):
        self.step = "google"

        # just googling
        system_prompt = PromptFactory.StandardPrompts.google_search_config_prompt

        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_description},
        ]
        result = self.search_engine.call_model(conversation)

        # summarize and pretify the result
        summarisation_prompt =(
            f"After googling the topic {task_description}, you found the results listed below."
            "Summarize the facts as brief as possible"
            "You MUST provide the links as sources for each fact."
            "Add tags in brackets to the facts to make them more searchable. For example: (Company X market trends), (Company X competitors), etc."
        )
        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": summarisation_prompt + f"Search Results:\n{result}"},
        ]
        result = self.thinking_engine.call_model(conversation)

        self.log(message = f"Agent {self.agent_id} of type {self.agent_type} googled:\n{task_description}\n\nand got:\n{result}", level = "info")

        # saving to the shared memory
        self._send_data_to_swarm(result)

        return result

        