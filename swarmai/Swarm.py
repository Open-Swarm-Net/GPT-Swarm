import numpy as np
import os
import threading
from datetime import datetime
import time

import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from swarmai.agents.GPTAgent import GPTAgent
from swarmai.agents.GPTAgent import ExplorerGPT
from swarmai.utils.CustomLogger import CustomLogger

from swarmai.utils.memory.DictSharedMemory import DictSharedMemory
from swarmai.utils.task_queue.PandasQueue import PandasQueue
from swarmai.utils.task_queue.Task import Task

from swarmai.agents.ManagerAgent import ManagerAgent

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
        "googler": ExplorerGPT,
        "analyst": GPTAgent,
    }

    TASK_TYPES = [
        Task.TaskTypes.synthesis,
        Task.TaskTypes.breakdown_to_subtasks,
        Task.TaskTypes.google_search,
        Task.TaskTypes.analysis
    ]

    TASK_ASSOCIATIONS = {
        "manager": [Task.TaskTypes.synthesis, Task.TaskTypes.breakdown_to_subtasks],
        "googler": [Task.TaskTypes.google_search],
        "analyst": [Task.TaskTypes.analysis]
    }

    def __init__(self, n_agents, agent_role_distribution):
        """Initializes the swarm.

        Args:
            n_agents (int): The number of agents in the swarm
            agent_role_distribution (dict): The dictionary that maps the agent roles to the weight of agents with that role
        """
        self.n_agents = n_agents
        self.agent_role_distribution = agent_role_distribution

        self.data_dir = Path(__file__).parent.parent.resolve() / "runs" / f"run_{self.challenge.problem_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # creating shared memory
        self.shared_memory_file = self.data_dir / 'shared_memory.json'
        self.shared_memory = DictSharedMemory(self.shared_memory_file)

        # creating task queue
        self.task_queue = PandasQueue(self.TASK_TYPES, self.WORKER_ROLES.keys(), self.TASK_ASSOCIATIONS)

        # creating the logger
        self.logger = CustomLogger(self.data_dir)

        # creating agents
        self.agents_ids = []
        self.agents = self._create_agents() # returns just a list of agents

        # some other attributes
        self.current_cycle = 0
        self.best_score = 0
        self.best_answer = ''

    def run_swarm(self, max_sec=10):
        """Runs the swarm for a given number of cycles or until the termination condition is met.
        """
        for agent in self.agents:
            agent.max_cycles = 500
            agent.name = f"Agent {agent.agent_id}" # inherited from threading.Thread => thread name
            self.log(f"Starting agent {agent.agent_id} with role {agent.agent_role}")
            agent.start()

        time.sleep(max_sec)
        for agent in self.agents:
            agent.ifRun = False

        for agent in self.agents:
            agent.join()

        self.log("All agents have finished their work")
        
        # finish execution
        self.log(f"Best score: {self.best_score}")
        self.log(f"Best answer: {self.best_answer}")


    def _create_agents(self):
        """Creates the tesnor of agents according to the tensor shape and the agent role distribution.
        For now just randomly allocating them in the swarm"""
        n_agents = np.prod(self.agents_tensor_shape)
        agent_keys = list(self.agent_role_distribution.keys())
        p=[self.agent_role_distribution[k] for k in agent_keys]

        # normalizing the distribution
        p = np.array(p) / np.sum(p)

        agent_roles_n = np.random.choice(
            agent_keys,
            size=n_agents,
            p=p,
        )

        agents = []
        for id, agent_role in enumerate(agent_roles_n):
            agent_id = id
            # need each agent to have its own challenge instance, because sometimes the agens submit the answers with infinite loops
            # also included a timeout for the agent's computation in the AgentBase class
            agents.append(self.WORKER_ROLES[agent_role](agent_id, agent_role, self, self.logger))
            self.agents_ids.append(agent_id)

        self.log(f"Created {len(agents)} agents with roles: {agent_roles_n}")
          
        return np.array(agents)

    def iterate_cycle(self):
        # Start the agents
        for agent in self.agents:
            agent.run_async()
        
        for agent in self.agents:
            agent.job.join(timeout = 60)

        # Save the state
        self.save_state()

    def add_shared_info(self, agent, data):
        """Adds data to the shared memory
        Args:
            agent (AgentBase): The agent that is adding the data
            data (dict): The data to add
        """
        # the mulithreading is handled by the shared memory
        try:
            score = data["score"]
            content = data["content"]
            agent_id = agent.agent_id
            agent_cycle = agent.cycle
            status = self.shared_memory.add_entry(score, agent_id, agent_cycle, content)

            # update the best score
            if score > self.best_score:
                self.best_score = score
                self.best_answer = content
            
            self.log(f"SOLSOL: Best solution so far: {self.best_score:.2f}")

            return status
        except Exception as e:
            self.log(f"Failed to add info {data} to the swarm: {e}", level="error")
            return False
    
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

