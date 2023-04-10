import numpy as np
import logging

from swarmai.utils.memory.DictSharedMemory import DictSharedMemory
from swarmai.agents.GPTAgent import GPTAgent
from swarmai.utils.CustomLogger import CustomLogger

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

        # creating shared memory
        self.shared_memory = DictSharedMemory()

        # creating the logger
        self.logger = self._logger_setup()

        # creating agents
        self.agents_ids = []
        self.agents = self._create_agents() # returns just a list of agents
        self.agents_coords = self._create_connectivity_matrix() # returns a matrix of agent coordinates

        # some other attributes
        self.current_cycle = 0


    def run_swarm(self, n_cycles):
        """Runs the swarm for a given number of cycles or until the termination condition is met.
        """
        for cycle_n in range(n_cycles):
            self.current_cycle = cycle_n
            self.logger.info(f"Cycle {cycle_n}")
            self.iterate_cycle()

            if self._termination_condition():
                break

    def _termination_condition(self):
        return False
        # Define your termination condition based on the problem or swarm state
        if self.shared_memory["best_score"] >= 1:
            self.log("Termination condition met!")
            return True
        else:
            return False

    def _create_agents(self):
        """Creates the tesnor of agents according to the tensor shape and the agent role distribution.
        For now just randomly allocating them in the swarm"""
        n_agents = np.prod(self.agents_tensor_shape)
        agent_keys = list(self.agent_role_distribution.keys())
        agent_roles_n = np.random.choice(
            agent_keys,
            size=n_agents,
            p=[self.agent_role_distribution[k] for k in agent_keys],
        )

        agents = []
        for id, agent_role in enumerate(agent_roles_n):
            agent_id = id
            agents.append(self.WORKER_ROLES[agent_role](agent_id, agent_role, self, self.shared_memory, self.challenge, self.logger))
            self.agents_ids.append(agent_id)

        np.random.shuffle(agents)

        self.logger.info(f"Created {len(agents)} agents with roles: {agent_roles_n}")
          
        return np.array(agents)
    
    def _create_connectivity_matrix(self):
        """Creates the coordinates of each agent in the tensor.
        For now just creating a list of coordinates of the same shape as self.agents
        """
        agents_roles = np.array([a.agent_role[0] for a in self.agents]).reshape(self.agents_tensor_shape)
        self.logger.info(f"Agents roles:\n{agents_roles}")
        return np.array(np.unravel_index(np.arange(np.prod(self.agents_tensor_shape)), self.agents_tensor_shape)).T
    
    def _logger_setup(self):
        """Creates the logger object"""
        log_folder = "logs"
        log_file = f"{log_folder}/swarm.log"

        # Create a custom logger instance and configure it
        logger = CustomLogger("SwarmLogger")
        logger.log_file = log_file
        logger.log_folder = log_folder
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        return logger

    def get_neighbours(self, agent_id):
        """For now just returning the coordinates of the ajacent nodes in the tensor.
        """
        agent_coords = self.agents_coords[self.agents_ids.index(agent_id)]
        distances = np.sum(np.abs(self.agents_coords - agent_coords), axis=1)
        neighbours = self.agents[distances <= 1]
        return neighbours
    
    def iterate_cycle(self):
        # Start the agents
        for agent in self.agents:
            agent.run_async()
        
        for agent in self.agents:
            agent.job.join()

        # Save the state
        self.save_state()

    def save_state(self):
        """Saves the state of the swarm to a file"""
        pass
