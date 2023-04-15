import numpy as np
import logging
import threading
from datetime import datetime

import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from swarmai.utils.memory.DictSharedMemory import DictSharedMemory
from swarmai.agents.GPTAgent import GPTAgent
from swarmai.agents.GPTAgent import ExplorerGPT
from swarmai.utils.CustomLogger import CustomLogger
from swarmai.challenges.python_challenges.PythonChallenge import PythonChallenge

class Swarm:
    """This class is responsible for managing the swarm of agents.

    The logic:
        1. The swarm gets a problem to solve and a reward function. The goal of the swarm is to maximize the reward.
        2. The swarm consists of agents that are connected in a tensor (for now). Nuber of neighbours is defined by the dimentionality of a tensor. Agent can ask the swarm for its neighbours.
        3. Agents have different roles.
        4. The computation is performed in cycles (for now). Each cycle is a step in the swarm. Cycles can have different purposes like computing, sharing, evaluating, etc. that define the agents' behaviour in the cycle.
        5. The swarm has a shared memory that the agents can query.

    The tasks of the swamr class are:
        1. Create and store the agents.
        2. Identify the connectivity matrix between agents and return the neighbours of each agent.
        3. Provide the agents with the access to the shared memory.
        4. Iterate the computational cycles and terminate the swarm when the goal is reached or the swarm is stuck.

    Swarm tips (to be extanded as we gather more experience):
        1. To avoid the swarm being stuck in a local maximum, the swarm should include agents with high and low exploration rates (models temperature).
        2. High reward solutions need to be reinfoced by the swarm, and the low reward solutions need to be punished, so that the swarm algorithm converges.
        3. The swarm architecture should have enough flexibility to allow for an emerging behaviour of the swarm (greater than the sum of its parts).

    TODO:
        - adaptation algorithm
        - vector database for the shared memory
    """

    WORKER_ROLES = {
        "python developer": GPTAgent,
        "explorer python": ExplorerGPT,
    }

    def __init__(self, challenge, agents_tensor_shape, agent_role_distribution):
        """Initializes the swarm.

        Args:
            challenge (implementation of ChallengeBase): The problem to solve.
            agents_tensor_shape (tuple): The shape of the tensor that defines the connectivity between agents.
            agent_role_distribution (dict): The weight of each role in the swarm.
        """
        self.challenge = challenge
        self.agents_tensor_shape = agents_tensor_shape
        self.agent_role_distribution = agent_role_distribution

        self.data_dir = Path(__file__).parent.parent.resolve() / "runs" / f"run_{self.challenge.problem_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # creating shared memory
        self.shared_memory_file = self.data_dir / 'shared_memory.json'
        self.shared_memory = DictSharedMemory(self.shared_memory_file)
        self.lock = threading.Lock() # need this one to accept shared memory updates from multiple threads

        # creating the logger
        self.logger = CustomLogger(self.data_dir)

        # creating agents
        self.agents_ids = []
        self.agents = self._create_agents() # returns just a list of agents
        self.agents_coords = self._create_connectivity_matrix() # returns a matrix of agent coordinates

        # some other attributes
        self.current_cycle = 0
        self.best_score = 0
        self.best_answer = ''

    def run_swarm(self, n_cycles):
        """Runs the swarm for a given number of cycles or until the termination condition is met.
        """
        for agent in self.agents:
            agent.max_cycles = n_cycles
            self.log(f"Starting agent {agent.agent_id} with role {agent.agent_role}")
            agent.start()
        for agent in self.agents:
            agent.join()

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
            agents.append(self.WORKER_ROLES[agent_role](agent_id, agent_role, self, self.shared_memory, self.challenge, self.logger))
            self.agents_ids.append(agent_id)

        np.random.shuffle(agents)

        self.log(f"Created {len(agents)} agents with roles: {agent_roles_n}")
          
        return np.array(agents)
    
    def _create_connectivity_matrix(self):
        """Creates the coordinates of each agent in the tensor.
        For now just creating a list of coordinates of the same shape as self.agents
        """
        agents_roles = np.array([a.agent_role[0] for a in self.agents]).reshape(self.agents_tensor_shape)
        self.log(f"Agents roles:\n{agents_roles}")
        return np.array(np.unravel_index(np.arange(np.prod(self.agents_tensor_shape)), self.agents_tensor_shape)).T

    def get_neighbours(self, agent_id):
        """For now just returning the coordinates of the ajacent nodes in the tensor.
        """
        agent_coords = self.agents_coords[self.agents_ids.index(agent_id)]
        distances = np.sum(np.abs(self.agents_coords - agent_coords), axis=1)
        neighbours = self.agents[distances <= 1] # inlcuding the agent itself, that's correct => self-memory
        return neighbours
    
    def iterate_cycle(self):
        # Start the agents
        for agent in self.agents:
            agent.run_async()
        
        for agent in self.agents:
            agent.job.join(timeout = 60)
            
        # TODO: need to find a deadlock (╯°□°）╯︵ ┻━┻). crappy hack ahead
        challenge_config = self.challenge.config_file_loc
        self.challenge = PythonChallenge(challenge_config)

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
            return status
        except Exception as e:
            self.log(f"Failed to add info {data} to the swarm: {e}", level="error")
            return False

    def save_state(self):
        """Saves the state of the swarm to a file"""
        
        # TODO: implement the state from which to resume the swarm

        # save a figure that presents the swarm performance
        fig = plt.figure(figsize=(5, 5))
        value_tensor = self.get_value_tensor()
        best_score = self.best_score
        sns.heatmap(value_tensor, annot=True, cbar=True, cmap="YlGnBu", vmin=0, vmax=1)
        plt.title(f"{self.current_cycle} => History best: {best_score:.2f}; Step average {np.mean(value_tensor):.2f}")
        fig_name = f"swarm_state_{self.current_cycle}.png"
        fig_path = Path(self.logger.log_folder, fig_name)
        fig.savefig(fig_path)
        plt.close(fig)

    def get_value_tensor(self):
        value_tensor = np.zeros(self.agents_tensor_shape)
        for agent, agent_coords in zip(self.agents, self.agents_coords):
            value_tensor[tuple(agent_coords)] = agent.result_score
        return value_tensor
    
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

