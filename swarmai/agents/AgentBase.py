from abc import ABC, abstractmethod
import threading
import queue
import time

from swarmai.utils.task_queue.Task import Task

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
        
    Attributes:
        agent_id (int): The unique identifier of the agent
        agent_type (str): The type of the agent, ex. worker, explorer, evaluator, etc.
        swarm (Swarm): The swarm object
        shared_memory (SharedMemoryBase implementation): The shared memory object
        challenge (Challenge implementation): The challenge object
        logger (Logger): The logger object
        max_cycles (int): The maximum number of cycles that the agent will run
    """

    def __init__(self, agent_id, agent_type, swarm, logger, max_cycles = 10):
        """Initialize the agent.
        """
        threading.Thread.__init__(self)
        ABC.__init__(self)
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.swarm = swarm
        self.shared_memory = self.swarm.shared_memory
        self.task_queue = self.swarm.task_queue

        self.logger = logger
        self.max_cycles = max_cycles

        # some mandatory components
        self.step = "init"
        self.task = None
        self.result = None
        self.internal_memory = None
        self.message_queue = queue.Queue()
        self.current_step = "init"
        self.ifRun = True
        self.cycle = 0

    def run(self):
        while self.ifRun:
            while self.task is None:
                self._get_task() # gets the task from the task queue
                if self.task is None:
                    time.sleep(15)

            self.job = AgentJob(self.agent_iteration, ())
            self.job.name = f"Agent {self.agent_id}, cycle {self.cycle}"
            self.job.start()
            self.job.join(timeout = 120)

            # there is no deadlock, but the agetns sometimes submit code with infinite loops, so need to kill the jobs
            if self.job.is_alive():
                self.log("Stuck. Dropping the thread.", level = "error")

            self.cycle += 1
            if self.cycle >= self.max_cycles:
                self.ifRun = False

    def agent_iteration(self):
        """Main iteration of the agent.
        """
        ifSuccess = self.perform_task()
        if ifSuccess:
            self._submit_complete_task()
            self.task = None

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
        """Main method of the agent that defines how it shares its results with the shared memory and the task queue
        """
        raise NotImplementedError
    
    def _submit_complete_task(self):
        self.task_queue.complete_task(self.task.task_id)

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

    def _get_task(self):
        """Gets the task from the task queue.
        It's not the job of the agent to decide which task to perform, it's the job of the task queue.
        """        
        task = self.task_queue.get_task(self)
        if task is not None:
            self.log(f"Got task: {task.task_description} of type: {task.task_type} with priority: {task.priority}" , level = "info")
        else:
            self.log(f"No task found. Waiting for the proper task", level = "debug")
            return None

        if not isinstance(task, Task):
            raise ValueError("The task is not a Task implementation.")
        
        self.task = task

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
        _ = self.shared_memory.add_entry(data)

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