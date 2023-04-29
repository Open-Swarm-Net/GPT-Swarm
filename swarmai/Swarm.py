import numpy as np
from datetime import datetime
import time
import yaml

from pathlib import Path

from swarmai.utils.CustomLogger import CustomLogger

from swarmai.utils.memory import VectorMemory
from swarmai.utils.task_queue.PandasQueue import PandasQueue
from swarmai.utils.task_queue.Task import Task

from swarmai.agents import ManagerAgent, GeneralPurposeAgent

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

    WORKER_ROLES = {
        "manager": ManagerAgent,
        "googler": GeneralPurposeAgent,
        "analyst": GeneralPurposeAgent,
    }

    TASK_TYPES = [
        Task.TaskTypes.summarisation,
        Task.TaskTypes.breakdown_to_subtasks,
        Task.TaskTypes.google_search,
        Task.TaskTypes.analysis
    ]

    TASK_ASSOCIATIONS = {
        "manager": [Task.TaskTypes.breakdown_to_subtasks, Task.TaskTypes.summarisation],
        "googler": [Task.TaskTypes.analysis, Task.TaskTypes.google_search],
        "analyst": [Task.TaskTypes.summarisation, Task.TaskTypes.analysis, Task.TaskTypes.google_search]
    }

    def __init__(self, swarm_config_loc):
        """Initializes the swarm.

        Args:
            agent_role_distribution (dict): The dictionary that maps the agent roles to the weight of agents with that role
        """
        self.swarm_config_loc = swarm_config_loc
        self._parse_swarm_config()

        # creating shared memory
        self.shared_memory_file = self.data_dir / 'shared_memory'
        self.shared_memory = VectorMemory(self.shared_memory_file)

        # creating task queue
        self.task_queue = PandasQueue(self.TASK_TYPES, self.WORKER_ROLES.keys(), self.TASK_ASSOCIATIONS)

        # creating the logger
        self.logger = CustomLogger(self.data_dir)

        # creating agents
        self.agents_ids = []
        self.agents = self._create_agents() # returns just a list of agents

    def _create_agents(self):
        """Creates the tesnor of agents according to the tensor shape and the agent role distribution.
        For now just randomly allocating them in the swarm"""
        agents = []
        counter = 0
        for key, val in self.agent_role_distribution.items():
            agent_role = key
            n = val
            for i in range(n):
                agent_id = counter
                counter += 1
                # need each agent to have its own challenge instance, because sometimes the agens submit the answers with infinite loops
                # also included a timeout for the agent's computation in the AgentBase class
                agents.append(self.WORKER_ROLES[agent_role](agent_id, agent_role, self, self.logger))
                self.agents_ids.append(agent_id)

        self.log(f"Created {len(agents)} agents with roles: {[agent.agent_type for agent in agents]}")
          
        return np.array(agents)

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

        # start the agents
        for agent in self.agents:
            agent.max_cycles = 50
            agent.name = f"Agent {agent.agent_id}" # inherited from threading.Thread => thread name
            self.log(f"Starting agent {agent.agent_id} with type {agent.agent_type}")
            agent.start()

        if self.timeout is not None:
            self.log(f"Swarm will run for {self.timeout} seconds")
            time.sleep(self.timeout)
        else:
            time.sleep(1000000000000000000000000)
        for agent in self.agents:
            agent.ifRun = False

        for agent in self.agents:
            agent.join()

        self.log("All agents have finished their work")

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
        
        self.timeout = config["swarm"]["timeout_min"]*60
        
        self.data_dir = Path(".", config["swarm"]["run_dir"])
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # getting the tasks
        self.role = config["task"]["role"]
        self.global_goal = config["task"]["global_goal"]
        self.goals = config["task"]["goals"]

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
        self.logger.log(level=level, msg= {'message': message})

