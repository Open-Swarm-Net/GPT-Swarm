import numpy as np
import uuid
import copy
from tqdm import tqdm
from pathlib import Path
import traceback
import concurrent.futures
import pickle
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import seaborn as sns

import logging

from gptswarm.swarm.Workers.TestWorker import TestWorker, ExplorerWorker

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
        "test": TestWorker,
        "explorer": ExplorerWorker,
    }

    CYCLES = ["compute", "share"]

    def __init__(self, challenge, tensor_shape, agent_role_distribution):
        """Initializes the swarm.

        Args:
            challenge (implementation of ChallengeBase): The problem to solve.
            tensor_shape (tuple): The shape of the tensor that defines the connectivity between agents.
            agent_role_distribution (dict): The weight of each role in the swarm.
        """
        self.challenge = challenge
        self.tensor_shape = tensor_shape
        self.agent_role_distribution = agent_role_distribution

        # creating the agetnts and the connectivity matrix
        self.agents_uuids = []
        self.agents = self._create_agents() # returns just a list of agents
        self.agents_coords = self._create_connectivity_matrix() # returns a matrix of agent coordinates

        # creating the shared memory, for now just a stupid lsit of scores and answers
        # TODO: make it a class for a potential vector database implementation
        self.max_memory_size = 20
        self.shared_memory = {
            "problem": self.challenge.get_problem(),
            "scores": [],
            "answers": [],
            "evaluations": [],
            "best_score": 0,
            "best_answer": "",
        }

        # creating the cycle state information and the cycle log
        self.cycle_state = {
            "cycle": 0,
            "cycle_type": "compute"
        }
        self.logger = None
        

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
            agents.append(self.WORKER_ROLES[agent_role](worker_uuid, self, self.challenge))
            self.agents_uuids.append(worker_uuid)

        np.random.shuffle(agents)
          
        return np.array(agents)
    
    def _create_connectivity_matrix(self):
        """Creates the coordinates of each agent in the tensor.
        For now just creating a list of coordinates of the same shape as self.agents
        """
        return np.array(np.unravel_index(np.arange(np.prod(self.tensor_shape)), self.tensor_shape)).T
    
    def _save_state(self):
        """Saves the shared momory of the swarm each cycle"""
        file_name = f"swarm_state_{self.cycle_state['cycle']}.pkl"
        file_path = Path(__file__).parent / "run" / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            pickle.dump(self.shared_memory, f)

        # also saving the image of swarm values
        fig = plt.figure(figsize=(5, 5))
        value_tensor = self.shared_memory["value_tensor"]
        best_score = self.shared_memory["best_score"]
        sns.heatmap(value_tensor, annot=True, cbar=True, cmap="YlGnBu", vmin=0, vmax=1)
        plt.title(f"{self.cycle_state['cycle']} => History best: {best_score:.2f}; Step average {np.mean(value_tensor):.2f}")
        fig_name = f"swarm_state_{self.cycle_state['cycle']}.png"
        fig_path = Path(__file__).parent / "run" / fig_name
        fig.savefig(fig_path)
        plt.close(fig)
    
    def get_neighbours(self, agent_uuid):
        """For now just returning the coordinates of the ajacent nodes in the tensor.
        """
        agent_coords = self.agents_coords[self.agents_uuids.index(agent_uuid)]
        distances = np.sum(np.abs(self.agents_coords - agent_coords), axis=1)
        neighbours = self.agents[distances <= 1]
        return neighbours
    
    def get_value_tensor(self):
        value_tensor = np.zeros(self.tensor_shape)
        for agent, agent_coords in zip(self.agents, self.agents_coords):
            value_tensor[tuple(agent_coords)] = agent.result_score
        return value_tensor
    
    def run_swarm(self, max_cycles=10):
        """Runs the swarm for a given number of cycles or until the termination condition is met.
        """
        while self.cycle_state["cycle"] < max_cycles and not self.termination_condition():
            self.log(f"Cycle {self.cycle_state['cycle']}", level="info")
            self.log(f"Shered memory: {self.shared_memory}", level="debug")
            self.iterate_cycle()

    def _compute_agent(self, agent):
        try:
            agent.perform_task(self.cycle_state["cycle_type"])
            return True
        except Exception as e:
            self.log(f"Error while computing agent: {e}", level="error")
            return False

    def iterate_cycle(self):
        """Iterates the swarm through the computational cycles.
        """
        if self.cycle_state["cycle_type"] == "compute":
            timeout_per_task = 45 # seconds
            results = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # sometimes the agents get frozen. Don't know why, yet, so implemented the timeout. Otherwise the swarm can get stuck
                futures = {executor.submit(self._compute_agent, agent): agent for agent in self.agents}

                # As the tasks complete, process the results
                for future in concurrent.futures.as_completed(futures, timeout=timeout_per_task*len(self.agents)):
                    agent = futures[future]
                    try:
                        result = future.result(timeout=timeout_per_task)
                        results.append(result)
                        self.log(f"Agent returned {result}", level="debug")
                    except concurrent.futures.TimeoutError:
                        self.log(f"Agent timed out", level="error")
                    except Exception as e:
                        self.log(f"Agent raised an exception: {e}", level="debug")      

        elif self.cycle_state["cycle_type"] == "share":         
            for agent in tqdm(self.agents):
                self._compute_agent(agent)
            self._save_state()
            self.log(f"Best solution:\n{self.shared_memory['best_answer']}", level="info")
        
        self.cycle_state["value_tensor"] = self.get_value_tensor()
        self.shared_memory["value_tensor"] = self.get_value_tensor()
        self.cycle_state["cycle"] += 1
        self.cycle_state["cycle_type"] = self._get_next_cycle_type()

    def _get_next_cycle_type(self):
        return self.CYCLES[(self.CYCLES.index(self.cycle_state["cycle_type"]) + 1) % len(self.CYCLES)]

    def termination_condition(self):
        return False
        # Define your termination condition based on the problem or swarm state
        if self.shared_memory["best_score"] >= 1:
            self.log("Termination condition met!")
            return True
        else:
            return False
        
    def add_to_shared_memory(self, score, result, evaluation):
        self.shared_memory["scores"].append(score)
        self.shared_memory["answers"].append(result)
        self.shared_memory["evaluations"].append(evaluation)

        if score > self.shared_memory["best_score"]:
            self.shared_memory["best_score"] = score
            self.shared_memory["best_answer"] = result

        # leave the top best results in the memory
        if len(self.shared_memory["scores"]) > self.max_memory_size:
            len_val = len(self.shared_memory["scores"])
            n_best = np.argsort(self.shared_memory["scores"])[-self.max_memory_size:]

            self.shared_memory["scores"] = [self.shared_memory["scores"][i] for i in n_best]
            self.shared_memory["answers"] = [self.shared_memory["answers"][i] for i in n_best]

    def log(self, agent="swarm", message="", level="info"):
        """Logs a message to the swarm log.
        Creates a logger if it doesn't exist yet.

        Logs the data to the log file.
        """
        self.log_file = Path("log.txt")
        if not self.log_file.parent.exists():
            self.log_file.parent.mkdir()
        if not self.log_file.exists():
            self.log_file.touch()

        if self.logger is None :
            # clear the log file
            with open(self.log_file, "w") as f:
                f.write("")
            
            self.logger = logging.getLogger("swarm")
            self.logger.setLevel(logging.DEBUG)
            fh = logging.FileHandler(self.log_file)
            fh.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

        message = f"{agent} - {message}"
        if level == "info":
            self.logger.info(message)
        elif level == "debug":
            self.logger.debug(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "critical":
            self.logger.critical(message)





                