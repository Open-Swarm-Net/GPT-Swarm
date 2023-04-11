from abc import ABC, abstractmethod
import threading
import queue
import sys

from swarmai.utils.memory.InternalMemoryBase import InternalMemoryBase

class AgentJob(threading.Thread):
    """A class that handles multithreading logic
    """
    def __init__(self, function, args):
        threading.Thread.__init__(self)
        self.function = function
        self.args = args
    
    def run(self):
        self.function(*self.args)

class AgentBase(ABC):
    """Abstract base class for agents in the swarm.
    
    - Agents are the entities that perform the task in the swarm.
    - Agents can have different roles and implementations, but they all need to implement a set of methods that would allow them to work together in a swarm.
    - Implements the threading. Thread class to allow the swarm to run in parallel.
    """

    def __init__(self, agent_id, agent_role, swarm, shared_memory, challenge, logger):
        """Initialize the agent.
        
        Args:
            agent_type (str): The type of the agent, ex. worker, explorer, evaluator, etc.
            swarm (Swarm): The swarm object.
            shared_memory (SharedMemoryBase implementation): The shared memory object.
            neighbor_queues (lsit): The queues to communicate with the neighbors.
            challenge (Challenge implementation): The challenge object.
            logger (Logger): The logger object.
        """
        super().__init__()
        self.agent_id = agent_id
        self.agent_role = agent_role
        self.swarm = swarm
        self.shared_memory = shared_memory
        self.challenge = challenge
        self.logger = logger

        # some mandatory components
        self.internal_memory = None
        self.neighbor_queues = []
        self.message_queue = queue.Queue()
        
        self.global_task = self.challenge.get_problem()

    def run_async(self):
        """Run the agent asynchronously
        """
        self.job = AgentJob(self.run, ())
        self.job.start()

    def run(self):
        """Run the agent
        """
        self._retrive_messages()
        self.perform_task()
        self.share()

    @abstractmethod
    def perform_task(self):
        """main method of the agent that defines the task it performs
        """
        raise NotImplementedError
    
    @abstractmethod
    def share(self):
        """Main method of the agent that defines how it shares its results with the neighbors
        """
        raise NotImplementedError
    
    def _retrive_messages(self):
        """Retrive messages from the neighbors.
        """
        for queue in self.neighbor_queues:
            if not queue.empty():
                message = queue.get()
                self.process_message(message)

    def _process_message(self, message):
        """Process the message from the neighbor.

        Args:
            message (dict): The message from the neighbor.
        """
        self.logger.debug(f"Agent {self.agent_id} received message: {message}")
        self.internal_memory.add_entry(message["score"], message["content"])
    
    def _send_data_to_neighbors(self, data):
        """Send data to the neighbors.

        Args:
            data (dict): The data to send: {"score": score, "content": content}
        """
        for queue in self.neighbor_queues:
            self.logger.debug(f"Agent {self.agent_id} sent message: {data}")
            queue.put(data)

    def _send_data_to_shared_memory(self, data):
        """Send data to the shared memory.

        Args:
            data (dict): The data to send.
        """
        with self.shared_memory.lock:
            self.shared_memory.lock.acquire(timeout = 30)
            try:
                self.shared_memory.add_entry(data)
            except Exception as e:
                self.logger.error(f"Agent {self.agent_id} failed to add entry to the shared memory: {e}")
            finally:
                self.shared_memory.lock.release()

    def reset(self):
        # Reset the necessary internal state while preserving memory
        self.should_run = True

    def stop(self):
        # Set the termination flag
        self.should_run = False