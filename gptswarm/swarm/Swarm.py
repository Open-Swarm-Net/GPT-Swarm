import numpy as np
import uuid

from gptswarm.swarm.Worker import TestWorker

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
    """

    WORKER_ROLES = {
        "test": TestWorker,
    }

    CYCLES = ["compute", "share"]

    def __init__(self, problem, reward_function, tensor_shape, agent_role_distribution):
        """Initializes the swarm.

        Args:
            problem (str): The problem to solve.
            reward_function (function): The reward function.
            tensor_shape (tuple): The shape of the tensor that defines the connectivity between agents.
            agent_role_distribution (dict): The weight of each role in the swarm.
        """
        self.problem = problem
        self.reward_function = reward_function
        self.tensor_shape = tensor_shape
        self.agent_role_distribution = agent_role_distribution

        # creating the agetnts and the connectivity matrix
        self.agents_uuids = []
        self.agents = self._create_agents() # returns just a list of agents
        self.agents_coords = self._create_connectivity_matrix() # returns a matrix of agent coordinates

        # creating the shared memory, for now just a stupid lsit of scores and answers
        self.shared_memory = {
            "problem": self.problem,
            "scores": [],
            "answers": [],
            "best_score": 0,
            "best_answer": "",
        }

        # creating the cycle state information and the cycle log
        self.cycle_state = {
            "cycle": 0,
            "cycle_type": "compute"
        }
        self.history = []
        

    def _create_agents(self):
        """Creates the tesnor of agents according to the tensor shape and the agent role distribution.
        For now just randomly allocating them in the swarm"""
        n_agents = np.prod(self.tensor_shape)
        agent_keys = list(self.agent_role_distribution.keys())
        agent_roles_n = np.random.choice(
            agent_keys,
            size=n_agents,
            p=[self.agent_role_distribution[k] for k in agent_keys],
        )

        agents = []
        for agent_role in agent_roles_n:
            worker_uuid = uuid.uuid4()
            agents.append(self.WORKER_ROLES[agent_role](worker_uuid, self, self.problem))
            self.agents_uuids.append(worker_uuid)

        np.random.shuffle(agents)
          
        return np.array(agents)
    
    def _create_connectivity_matrix(self):
        """Creates the coordinates of each agent in the tensor.
        For now just creating a list of coordinates of the same shape as self.agents
        """
        return np.array(np.unravel_index(np.arange(np.prod(self.tensor_shape)), self.tensor_shape)).T
    
    def get_neighbours(self, agent_uuid):
        """For now just returning the coordinates of the ajacent nodes in the tensor.
        """
        agent_coords = self.agents_coords[self.agents_uuids.index(agent_uuid)]
        distances = np.sum(np.abs(self.agents_coords - agent_coords), axis=1)
        neighbours = self.agents[distances <= 1]
        return neighbours
    
    def run_swarm(self, max_cycles=10):
        """Runs the swarm for a given number of cycles or until the termination condition is met.
        """
        while self.cycle_state["cycle"] < max_cycles and not self.termination_condition():
            print(f"Cycle {self.cycle_state['cycle']}")
            self.iterate_cycle()

    def iterate_cycle(self):
        """Iterates the swarm through the computational cycles.

        TODO parallelize the computation of the agents
        """
        for agent in self.agents:
            agent.perform_task(self.cycle_state["cycle_type"])
        self.history.append(self.cycle_state | self.shared_memory)
        
        next_cycle_type = self._get_next_cycle_type()
        self.cycle_state["cycle"] += 1
        self.cycle_state["cycle_type"] = next_cycle_type

    def _get_next_cycle_type(self):
        return self.CYCLES[(self.CYCLES.index(self.cycle_state["cycle_type"]) + 1) % len(self.CYCLES)]

    def termination_condition(self):
        # Define your termination condition based on the problem or swarm state
        if self.shared_memory["best_score"] > 0.9:
            print("Termination condition met!")
            return True
        else:
            return False
        
    def add_to_shared_memory(self, score, result):
        self.shared_memory["scores"].append(score)
        self.shared_memory["answers"].append(result)

        if score > self.shared_memory["best_score"]:
            self.shared_memory["best_score"] = score
            self.shared_memory["best_answer"] = result