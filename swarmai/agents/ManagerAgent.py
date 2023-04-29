import os
import openai
import re

from swarmai.agents.AgentBase import AgentBase
from swarmai.utils.ai_engines.GPTConversEngine import GPTConversEngine
from swarmai.utils.task_queue.Task import Task
from swarmai.utils.PromptFactory import PromptFactory

class ManagerAgent(AgentBase):
    """Manager agent class that is responsible for breaking down the tasks into subtasks and assigning them into the task queue.

    Attributes:
        - 
    """

    def __init__(self, agent_id, agent_type, swarm, logger):
        super().__init__(agent_id, agent_type, swarm, logger)
        self.engine = GPTConversEngine("gpt-3.5-turbo", 0.5, 1000)
        
        self.TASK_METHODS = {
            Task.TaskTypes.summarisation: self.summarisation,
            Task.TaskTypes.breakdown_to_subtasks: self.breakdown_to_subtasks,
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

    def summarisation(self, task_description):
        """Summarises the content of the shared memory regarding a specific topic.
        """
        self.step = "summarisation"

        # first, search the memory for the topic
        memory_search_results_list = self._search_memory(task_description)

        # second, summarise the results
        summary = self._summarise_results(task_description, memory_search_results_list)

        # add to shared memory
        self._send_data_to_swarm(
            data = summary
        )

    def _search_memory(self, task_description):
        """Searches the internal memory for a specific topic.
        Returns a string with the results.
        """
        self.step = "_search_memory"
        # first, search the shared memory for the topic
        base_memory_search_prompt = PromptFactory.StandardPrompts.memory_search_prompt
        fpormatting_prompt_list = "The output MUST be formatted in a following way [['query1'; 'query2'; ...]]"

        conversation = [
            {"role": "system", "content": base_memory_search_prompt + fpormatting_prompt_list},
            {"role": "user", "content": "Task to research:\n" + task_description}
        ]

        querries_unformatted = self.engine.call_model(conversation)

        # parse the querries
        querries_unformatted = re.search(r"\[\[.*\]\]", querries_unformatted)
        if querries_unformatted is None:
            return []
        
        querries_unformatted = querries_unformatted.group(0)
        querries_unformatted = querries_unformatted.replace("[", "").replace("]", "").replace("'", "").strip()
        querries = querries_unformatted.split(";")

        # second, search the memory for each query
        memory_search_results = []
        for query_i in querries:
            self.log(message = f"Searching the memory for the query {query_i}", level = "info")
            results_list = self.shared_memory.search_memory(query_i)
            if results_list is None:
                self.log(message = f"Could not find any results for the query {query_i}", level = "info")
                continue
            for result_i in results_list:
                result_i = result_i.replace("\n", "").replace("\r", "").replace("\t", "").strip()
                self.log(message=f"For the query {query_i} found the result {result_i}", level="debug")
                memory_search_results.append(result_i)

        return memory_search_results

    def _summarise_results(self, task_description, results_list):
        """Summarises the results of the search.
        """
        self.step = "_summarise_results"
        summarisation_base_prompt = PromptFactory.StandardPrompts.summarisation_for_task_prompt

        user_prompt = (
            "Global Tasks:\n" + task_description + "\n"
            "Results:\n" + "\n".join(results_list) + "\n"
        )

        conversation = [
            {"role": "system", "content": summarisation_base_prompt},
            {"role": "user", "content": user_prompt}
        ]

        summarisation = self.engine.call_model(conversation)

        return summarisation


    def breakdown_to_subtasks(self, main_task_description):
        """Breaks down the main task into subtasks and adds them to the task queue.
        """
        self.step = "breakdown_to_subtasks"

        task_breakdown_prompt = PromptFactory.StandardPrompts.task_breakdown
        allowed_subtusk_types = [str(t_i) for t_i in self.swarm.TASK_TYPES]
        allowed_subtusk_types_str = "\nFollowing subtasks are allowed:" + ", ".join(allowed_subtusk_types)
        output_format = f"\nThe output MUST be ONLY a list of subtasks in the following format: [[(subtask_type; subtask_description; priority in 0 to 100), (subtask_type; subtask_description; priority in 0 to 100), ...]]"
        one_shot_example = (
            "\nExample: \n"
            "Task: Write a report about the current state of the project.\n"
            "Subtasks:\n"
            f"[[({allowed_subtusk_types[0]}; Find information about the project; 50), ({allowed_subtusk_types[-1]}; Write a conclusion; 5)]]\n"
        )

        task_prompt = (
            "Task: " + main_task_description + "\n"
            "Subtasks:"
        )

        # generate a conversation
        conversation = [
            {"role": "system", "content": task_breakdown_prompt + allowed_subtusk_types_str + output_format + one_shot_example},
            {"role": "user", "content": task_prompt}
        ]

        result = self.engine.call_model(conversation)
        result = result.replace("\n", "").replace("\r", "").replace("\t", "").strip()

        # parse the result

        # first, find the substring enclosed in [[]]
        subtasks_str = re.search(r"\[\[.*\]\]", result)
        try:
            subtasks_str = subtasks_str.group(0)
        except:
            raise Exception(f"Failed to parse the result {result}")

        # then, find all substrings enclosed in ()
        subtasks = []
        for subtask_str_i in re.findall(r"\(.*?\)", subtasks_str):
            subtask_str_i = subtask_str_i.replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("'", "").strip()
            result_split = subtask_str_i.split(";")

            try:
                subtask_type = result_split[0].strip()
            except:
                continue

            try:
                subtask_description = result_split[1].strip()
            except:
                continue

            try:
                prio_int = int(result_split[2].strip())
            except:
                prio_int = 0

            subtasks.append((subtask_type.strip(), subtask_description.strip(), prio_int))

        # add subtasks to the task queue
        self._add_subtasks_to_task_queue(subtasks)

        # add to shared memory
        self._send_data_to_swarm(
            data = f"Task '{main_task_description}' was broken down into {len(subtasks)} subtasks: {subtasks}"
        )

    def _add_subtasks_to_task_queue(self, subtask_list: list):
        self.step = "_add_subtasks_to_task_queue"
        for task_i in subtask_list:
            try:
                # generating a task object
                taks_obj_i = Task(
                    priority=task_i[2],
                    task_type=task_i[0],
                    task_description=f"For the purpose of '{self.task.task_description.replace('For the purpose of ', '')}': {task_i[1]}",
                )
                self.swarm.task_queue.add_task(taks_obj_i)
            except:
                continue
