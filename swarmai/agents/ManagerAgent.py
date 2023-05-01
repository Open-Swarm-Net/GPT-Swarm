import os
import openai
import re
import random
import json

from swarmai.agents.AgentBase import AgentBase
from swarmai.utils.ai_engines.GPTConversEngine import GPTConversEngine
from swarmai.utils.task_queue.Task import Task
from swarmai.utils.PromptFactory import PromptFactory

class ManagerAgent(AgentBase):
    """Manager agent class that is responsible for breaking down the tasks into subtasks and assigning them into the task queue.
    """

    def __init__(self, agent_id, agent_type, swarm, logger):
        super().__init__(agent_id, agent_type, swarm, logger)
        self.engine = GPTConversEngine("gpt-3.5-turbo", 0.25, 2000)
        
        self.TASK_METHODS = {
            Task.TaskTypes.report_preparation: self.report_preparation,
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
            self.log(message = f"Agent {self.agent_id} of type {self.agent_type} failed to perform the task {self.task.task_description[:20]}...{self.task.task_description[-20:]} of type {self.task.task_type} with error {e}", level = "error")
            return False

    def share(self):
        pass

    def report_preparation(self, task_description):
        """The manager agent prepares a report.
        For each goal of the swarm:
            1. It reads the current report.
            2. It analyses which information is missing in the report to solve the global task.
            3. Then it tries to find this information in the shared memory
            Updating report:
                If it finds the information:
                    it adds it to the report
                else:
                    it adds the task to the task queue

                Finally: resets the report preparation task
        """
        global_goal = self.swarm.global_goal
        goals = self.swarm.goals.copy()
        random.shuffle(goals)

        for _, goal in enumerate(goals):
            idx = self.swarm.goals.index(goal)
            report_json = self._get_report_json()

            # find the goal. The format is the following: {1: {"Question": goal_i, "Answer": answer_i}, 2:...}
            if idx in report_json:
                prev_answer = report_json[idx]["Answer"]
            else:
                prev_answer = ""

            missing_information_list = self._analyse_report(global_goal, goal, prev_answer)
                
            for el in missing_information_list:
                self._add_subtasks_to_task_queue([('google_search', f"For the purpose of {goal}, find information about {el}", 50)])

            # update the report
            info_from_memory = self.shared_memory.ask_question(f"For the purpose of {global_goal}, try to find information about {goal}. Summarise it shortly and indclude web-lins of sources. Be an extremely critical analyst!.") 
            if info_from_memory is None:
                info_from_memory = ""
            conversation = [
                {"role": "system", "content": PromptFactory.StandardPrompts.summarisation_for_task_prompt },
                {"role": "user", "content": info_from_memory + prev_answer + f"\nUsing all the info above answer the question:\n{goal}\n"},
            ]
            summary = self.engine.call_model(conversation)

            # add to the report
            report_json = self._get_report_json()
            report_json[idx] = {"Question": goal, "Answer": summary}
            self.swarm.interact_with_output(json.dumps(report_json), method="write")

        self.swarm.create_report_qa_task()

    def _get_report_json(self):
        report = self.swarm.interact_with_output("",  method="read")
        if report == "":
            report = "{}"
        # parse json
        report_json = json.loads(report)
        return report_json

    def _analyse_report(self, global_goal, goal, prev_answer):
        """Checks what information is missing in the report to solve the global task.
        """
        prompt = (
            f"Our global goal is:\n{global_goal}\n\n"
            f"The following answer was prepared to solve this goal:\n{prev_answer}\n\n"
            f"Which information is missing in the report to solve the following subgoal:\n{goal}\n\n"
            f"If no information is missing or no extention possible, output: ['no_missing_info']"
            f"Provide a list of specific points that are missing from the report to solve a our subgoal.\n\n"
        )
        conversation = [
            {"role": "user", "content": prompt},
        ]
        missing_information_output = self.engine.call_model(conversation)

        # parse the output
        missing_information_output = re.search(r"\[.*\]", missing_information_output)
        if missing_information_output is None:
            return []
        missing_information_output = missing_information_output.group(0)
        missing_information_output = missing_information_output.replace("[", "").replace("]", "").replace("'", "").strip()
        missing_information_list = missing_information_output.split(",")

        if missing_information_list == ["no_missing_info"]:
            return []
        
        if len(missing_information_list) == 1:
            missing_information_list = missing_information_output.split(";")

        return missing_information_list

    def _repair_json(self, text):
        """Reparing the output of the model to be a valid JSON.
        """
        prompt = (
            "Act as a professional json repairer. Repair the following JSON if needed to make sure it conform to the correct json formatting.\n"
            "Make sure it's a single valid JSON object.\n"
            """The report ABSOLUTELY MUST be in the following JSON format:  {[{"Question": "question1", "Answer": "answer1", "Sources": "web links of the sources"}, {"Question": "question2", "Answer": "answer2", "Sources": "web links of the sources"},...]}"""
        )
        conversation = [
            {"role": "user", "content": prompt+text},
        ]
        return self.engine.call_model(conversation)

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
        subtasks_str = re.search(r"\[.*\]", result)
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
        self.log(
            message=f"Task:\n'{main_task_description}'\n\nwas broken down into {len(subtasks)} subtasks:\n{subtasks}",
        )
        # self._send_data_to_swarm(
        #     data = f"Task '{main_task_description}' was broken down into {len(subtasks)} subtasks: {subtasks}"
        # )
        return subtasks

    def _add_subtasks_to_task_queue(self, subtask_list: list):
        if len(subtask_list) == 0:
            return

        self.step = "_add_subtasks_to_task_queue"
        summary_conversation = [
            {"role": "system", "content": "Be very concise and precise when summarising the global task. Focus on the most important aspects of the global task to guide the model in performing a given subtask. Don't mention any subtasks but only the main mission as a guide."},
            {"role": "user", "content": f"""Global Task:\n{self.task.task_description}\nSubtasks:\n{"||".join([x[1] for x in subtask_list])}\nSummary of the global task:"""},
        ]
        task_summary = self.engine.call_model(summary_conversation)
        for task_i in subtask_list:
            try:
                # generating a task object
                taks_obj_i = Task(
                    priority=task_i[2],
                    task_type=task_i[0],
                    task_description=f"""For the purpose of '{task_summary}' Perform ONLY the following task: {task_i[1]}""",
                )
                self.swarm.task_queue.add_task(taks_obj_i)
            except:
                continue
