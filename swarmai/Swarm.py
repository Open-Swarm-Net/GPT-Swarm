from collections import defaultdict

import numpy as np
from datetime import datetime
import time
import yaml
import threading
import os
import json
import shutil

from pathlib import Path

from swarmai.utils.CustomLogger import CustomLogger

from swarmai.utils.memory import VectorMemory
from swarmai.utils.task_queue.PandasQueue import PandasQueue
from swarmai.utils.task_queue.Task import Task

from swarmai.agents import AGENT_ROLES


class Swarm:
    """This class is responsible for managing the swarm of agents.

    The logic:
        1. User submits a problem to the swarm
        2. The swarm consists of agents, shared memory and a task queue.
        3. Agents have different roles.
        4. Manager agents are responsible for creating tasks and assigning them to the task queue.
        5. The swarm has a shared memory that the agents can query.

    The tasks of the swarm class are:
        1. Create and store the agents
        2. Start the swarm
        3. Provide the agents with the access to the shared memory and the task queue
        4. Maintain stuck agents
        5. Logging

    Swarm tips (to be extanded as we gather more experience):
        1. To avoid the swarm being stuck in a local maximum, the swarm should include agents with high and low exploration rates (models temperature).
        2. High reward solutions need to be reinfoced by the swarm, and the low reward solutions need to be punished, so that the swarm algorithm converges.
        3. The swarm architecture should have enough flexibility to allow for an emerging behaviour of the swarm (greater than the sum of its parts).

    TODO:
        - adaptation algorithm (dynamically change the number of agents and their roles)
        - vector database for the shared memory
    """

    def __init__(self, swarm_config_loc, agents_config_loc):
        """Initializes the swarm.

        Args:
            swarm_config_loc (str): Path to the swarm config file, which contains the swarm parameters.
            agents_config_loc (str): Path to the agents config file, which contains the agents parameters.
        """

        self.swarm_config_loc = swarm_config_loc
        self.agents_config_loc = agents_config_loc
        self._parse_swarm_config()
        self._parse_agents_config()

        # creating shared memory
        self.shared_memory_file = self.data_dir / 'shared_memory'
        self.shared_memory = VectorMemory(self.shared_memory_file)
        self.output_file = str((self.data_dir / 'output.txt').resolve())
        with open(self.output_file, 'w') as f:
            f.write("")

        out_json = Path(str(self.output_file).replace(".txt", ".json"))
        if out_json.exists():
            with open(self.output_file, 'w') as f:
                f.write("")

        out_pretty = Path(str(self.output_file).replace(".txt", "_pretty.txt"))
        if out_pretty.exists():
            with open(self.output_file, 'w') as f:
                f.write("")

        # creating task queue
        self.task_queue = PandasQueue(self.tasks_in_use, self.agents_in_use, self.task_associations)

        # creating the logger
        self.logger = CustomLogger(self.data_dir)

        # creating agents
        self.agents_ids = []
        self.agents = self._create_agents()  # returns just a list of agents

        # get a lock
        self.lock = threading.Lock()

    def _create_agents(self):
        """Creates the tesnor of agents according to the tensor shape and the agent role distribution.
        For now just randomly allocating them in the swarm"""
        agents = []
        counter = 0
        for key, val in self.agent_role_distribution.items():
            agent_role = key
            agent_role = self._check_keys_and_agents(agent_role)

            n = val
            for _ in range(n):
                agent_id = counter
                counter += 1
                # need each agent to have its own challenge instance, because sometimes the agens submit the answers with infinite loops
                # also included a timeout for the agent's computation in the AgentBase class
                agents.append(AGENT_ROLES[agent_role](agent_id, agent_role, self, self.logger))
                self.agents_ids.append(agent_id)

        self.log(f"Created {len(agents)} agents with roles: {[agent.agent_type for agent in agents]}")

        return np.array(agents)

    def _check_keys_and_agents(self, agent_role):
        # if GOOGLE_API_KEY and GOOGLE_CSE_ID are not in os.environ, then the googler agent will be treated as a general purpose agent
        if agent_role == "googler" and ("GOOGLE_API_KEY" not in os.environ or "GOOGLE_CSE_ID" not in os.environ):
            agent_role = "analyst"

        return agent_role

    def run_swarm(self):
        """Runs the swarm for a given number of cycles or until the termination condition is met.
        """
        # add the main task to the task queue
        n_initial_manager_tasks = len(self.goals)
        for i in range(n_initial_manager_tasks):
            task_i = Task(
                priority=100,
                task_type=Task.TaskTypes.breakdown_to_subtasks,
                task_description=f"Act as:\n{self.role}Gloabl goal:\n{self.global_goal}\nYour specific task is:\n{self.goals[i]}"
            )
            self.task_queue.add_task(task_i)
            self.create_report_qa_task()

        # start the agents
        for agent in self.agents:
            agent.max_cycles = 50
            agent.name = f"Agent {agent.agent_id}"  # inherited from threading.Thread => thread name
            self.log(f"Starting agent {agent.agent_id} with type {agent.agent_type}")
            agent.start()

        if self.timeout is not None:
            self.log(f"Swarm will run for {self.timeout} seconds")
            time.sleep(self.timeout)
        else:
            time.sleep(1000000000000000000000000)
        self.stop()

        self.log("All agents have finished their work")

    def create_report_qa_task(self):
        """Creates a task that will be used to evaluate the report quality.
        Make it as a method, because it will be called by the manager agent too.
        """
        task_i = Task(
            priority=50,
            task_type=Task.TaskTypes.report_preparation,
            task_description=f"Prepare a final report about a global goal."
        )
        self.task_queue.add_task(task_i)

    def stop(self):
        for agent in self.agents:
            agent.ifRun = False
        for agent in self.agents:
            agent.join()

    def _parse_agents_config(self):
        """Parses the agents configuration file and setup it's tasks

        agents:
          - name: manager
            tasks:
              - breakdown_to_subtasks
              - report_preparation
          - name: googler
            tasks:
              - google_search
          - name: analyst
            tasks:
              - analysis
          - name: crunchbase_searcher
            tasks:
              - crunchbase_search

        """

        file = self.agents_config_loc
        with open(file, "r") as f:
            config = yaml.safe_load(f)

        agents_in_use = []
        tasks_in_use = []
        task_associations = defaultdict(list)

        all_task_types = Task.TaskTypes.get_all_task_types()
        all_agent_roles = AGENT_ROLES.keys()

        for agent in config["agents"]:
            agent_name = agent["name"]
            if agent_name not in all_agent_roles:
                raise ValueError(f"Agent {agent_name} is not supported. Supported agents are: {all_agent_roles}")
            agents_in_use.append(agent["name"])
            for agent_task in agent["tasks"]:
                if agent_task not in all_task_types:
                    raise ValueError(f"Task {agent_task} is not supported. Supported tasks are: {all_task_types}")
                tasks_in_use.append(agent_task)
                task_associations[agent_task].append(agent_name)

        if len(agents_in_use) == 0:
            raise ValueError(f"No agents are specified in the config file {file}")

        if len(tasks_in_use) == 0:
            raise ValueError(f"No tasks are specified in the config file {file}")

        self.agents_in_use = agents_in_use
        self.tasks_in_use = tasks_in_use
        self.task_associations = task_associations

    def _parse_swarm_config(self):
        """Parses the swarm configuration file and returns the agent role distribution.
        It's a yaml file with the following structure:

        swarm:
            agents: # supported: manager, analyst, googler
                - type: manager
                n: 5
                - type: analyst
                n: 10
            timeout: 10m
            run_dir: /tmp/swarm
        task:
            role: |
                professional venture capital agency, who has a proven track reckord of consistently funding successful startups
            global_goal: |
                A new startup just send us their pitch. Find if the startup is worth investing in. The startup is in the space of brain computer interfaces.
                Their value proposition is to provide objective user experience research for new games beased directly on the brain activity of the user.
            goals:
                - Generate a comprehensive description of the startup. Find any mentions of the startup in the news, social media, etc.
                - Find top companies and startups in this field. Find out their locations, raised funding, value proposition, differentiation, etc.
        """
        file = self.swarm_config_loc
        with open(file, "r") as f:
            config = yaml.safe_load(f)

        self.agent_role_distribution = {}
        for agent in config["swarm"]["agents"]:
            self.agent_role_distribution[agent["type"]] = agent["n"]

        self.timeout = config["swarm"]["timeout_min"] * 60

        self.data_dir = Path(".", config["swarm"]["run_dir"]).resolve()
        # first, try to delete the directory with all the data
        try:
            for dir_i in self.data_dir.iterdir():
                shutil.rmtree(dir_i)
        except Exception:
            pass

        self.data_dir.mkdir(parents=True, exist_ok=True)

        # getting the tasks
        self.role = config["task"]["role"]
        self.global_goal = config["task"]["global_goal"]
        self.goals = config["task"]["goals"]

    def interact_with_output(self, message, method="write"):
        """Writed/read the report file.
        Needed to do it as one method due to multithreading.
        """
        with self.lock:
            if method == "write":
                # completely overwriting the file
                with open(self.output_file, "w") as f:
                    f.write(message)
                    f.close()

                # try to write it to json. can somtimes be malformated
                out_json = str(self.output_file).replace(".txt", ".json")
                message_dict = json.loads(message)
                with open(out_json, "w") as f:
                    try:
                        json.dump(message_dict, f, indent=4)
                    except:
                        pass
                    f.close()

                # pretty output. take json and outpout it as a text but with sections
                out_pretty = str(self.output_file).replace(".txt", "_pretty.txt")
                with open(out_pretty, "w") as f:
                    for _, value in message_dict.items():
                        f.write("========================================\n")
                        f.write("========================================\n")
                        for key, value in value.items():
                            f.write(f"**{key}**:\n{value}\n\n")
                        f.write("\n")

                    f.close()

                return message

            elif method == "read":
                # reading the report file
                with open(self.output_file, "r") as f:
                    message = f.read()
                    f.close()
                    return message

            else:
                raise ValueError(f"Unknown method {method}")

    def log(self, message, level="info"):
        level = level.lower()
        if level == "info":
            level = 20
        elif level == "debug":
            level = 10
        elif level == "warning":
            level = 30
        elif level == "error":
            level = 40
        elif level == "critical":
            level = 50
        else:
            level = 0
        self.logger.log(level=level, msg={'message': message})
