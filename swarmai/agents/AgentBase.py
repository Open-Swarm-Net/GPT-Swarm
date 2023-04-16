from abc import ABC, abstractmethod
import threading
import queue

from swarmai.challenges.python_challenges.PythonChallenge import PythonChallenge

class AgentJob(threading.Thread):
    """A class that handles multithreading logic
    """
    def __init__(self, function, args):
        threading.Thread.__init__(self)
        self.function = function
        self.args = args
    
    def run(self):
        self.function(*self.args)

class AgentBase(ABC, threading.Thread):
    """Abstract base class for agents in the swarm.
    
    - Agents are the entities that perform the task in the swarm.
    - Agents can have different roles and implementations, but they all need to implement a set of methods that would allow them to work together in a swarm.
    - Implements the threading. Thread class to allow the swarm to run in parallel.
    """

    def __init__(self, agent_id, agent_role, swarm, shared_memory, challenge, logger, max_cycles = 10):
        """Initialize the agent.
        
        Args:
            agent_type (str): The type of the agent, ex. worker, explorer, evaluator, etc.
            swarm (Swarm): The swarm object.
            shared_memory (SharedMemoryBase implementation): The shared memory object.
            neighbor_queues (lsit): The queues to communicate with the neighbors.
            challenge (Challenge implementation): The challenge object.
            logger (Logger): The logger object.
        """
        threading.Thread.__init__(self)
        ABC.__init__(self)
        self.agent_id = agent_id
        self.agent_role = agent_role
        self.swarm = swarm
        self.shared_memory = shared_memory
        self.challenge = challenge
        self.logger = logger
        self.max_cycles = max_cycles

        # some mandatory components
        self.internal_memory = None
        self.neighbor_queues = []
        self.message_queue = queue.Queue()
        self.current_step = "init"
        self.ifRun = True
        self.cycle = 0
        
        self.global_task = self.challenge.get_problem()

    def run(self):
        while self.ifRun:
            self.job = AgentJob(self.agent_iteration, ())
            self.job.name = f"Agent {self.agent_id}, cycle {self.cycle}"
            self.job.start()
            self.job.join(timeout = 120)

            # there is no deadlock, but the agetns sometimes submit code with infinite loops, so need to kill the jobs
            if self.job.is_alive():
                self.log("Stuck. Restarting the challenge object.", level = "error")
                challenge_config = self.challenge.config_file_loc
                self.challenge = PythonChallenge(challenge_config)

            self.cycle += 1
            if self.cycle >= self.max_cycles:
                self.ifRun = False

    def agent_iteration(self):
        """Main iteration of the agent.
        """
        self._retrive_messages()
        self.perform_task()
        self.share()

    def terminate(self):
        """Terminate the agent
        """
        self.ifRun = False

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
        # can't use .qsize of .empty() because they are not reliable
        queue_full = True
        while queue_full:
            try:
                message = self.message_queue.get(timeout=0.1)
                self._process_message(message)
                self.message_queue.task_done()
            except queue.Empty:
                queue_full = False
            except Exception as e:
                self.log(f"Error while processing the message: {e}", level = "error")

    def _process_message(self, message):
        """Process the message from the neighbor.

        Args:
            message (dict): The message from the neighbor.
        """
        self.log(f"Received message: {message}", level="debug")
        self.internal_memory.add_entry(message["score"], message["content"])
    
    def _send_data_to_neighbors(self, data):
        """Send data to the neighbors.

        Args:
            data (dict): The data to send: {"score": score, "content": content}
        """
        for queue in self.neighbor_queues:
            self.log(f"Sent message: {data}", level = "debug")
            queue.put(data)

    def _send_data_to_swarm(self, data):
        """Send data to the shared memory.

        Args:
            data (dict): The data to send: {"score": score, "content": content}
        """
        self.log(f"To shared memory: {data}", level = "debug")
        _ = self.swarm.add_shared_info(self, data) # the lock is set in the swarm

    def add_neighbour(self, neighbour_agent):
        """Add a neighbor to the agent.

        Args:
            queue (Queue): The queue to communicate with the neighbor.
        """
        self.log(f"Added neighbour: {neighbour_agent.agent_id}", level = "debug")
        self.neighbor_queues.append(neighbour_agent.message_queue)

    def reset(self):
        # Reset the necessary internal state while preserving memory
        self.should_run = True

    def stop(self):
        # Set the termination flag
        self.should_run = False

    def log(self, message, level = "info"):
        """Need to extend the logging a bit to include the agent id and the step name.
        Otherwise too hard to debug.
        """
        if isinstance(level, str):
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

        message = {"agent_id": self.agent_id, "cycle": self.cycle, "step": self.current_step, "message": message}
        self.logger.log(level, message)