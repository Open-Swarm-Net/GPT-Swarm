from abc import ABC, abstractmethod

from gptswarm.utils.GPTAgent import GPTAgent
from gptswarm.utils.LangchainAgent import LangchainAgent

class WorkerBase:
    """The worker class is an abstract class for single entity in the swarm that performs different taks.
    Workers can have different roles, but they all need to implement a set of methods that would allow them to work together in a swarm.
    """
    AGENT_TYPES ={
        "gpt": GPTAgent,
        "langchain": LangchainAgent,
    }

    def __init__(self, worker_uuid, swarm, challenge):
        self.worker_uuid = worker_uuid
        self.swarm = swarm

        # getting the challenge
        self.challenge = challenge
        self.global_task = self.challenge.get_problem()

        # getting the list of neighbours: [worker_obj, worker_obj, ...]
        self.neighbours = [] # at the init stage the neighbours are not known

        # defining containers for the data
        # expected form of the conversation: [{"role": "user", "content": str}, {"role": "assistant", "content": str}, ...]
        self.conversation = []
        self.incoming_messages = [] # lsit of strings! not dicts! why, though?
        self.max_memory_size = 4
        self.result = {"role": "assistant", "content": ""}
        self.result_score = 0
        self.evaluation = ''

    @abstractmethod
    def perform_task(self, cycle_type):
        pass

    @abstractmethod
    def share(self):
        pass

    @abstractmethod
    def _self_evaluate(self):
        pass

    def add_message(self, result, evaluation):
        """Receives a message from another worker.
        """
        if isinstance(result, dict):
            result = result["content"]
        if isinstance(evaluation, dict):
            evaluation = evaluation["content"]

        message = f"Potential solution: {result} \nEvaluation: {evaluation}"
        
        # add in a circular buffer fashion
        self.incoming_messages.append(message)
        while len(self.incoming_messages) > self.max_memory_size:
            self.incoming_messages.pop(0)

    def log(self, message, level="info"):
        """Logs a message. The swarm handles the logging and verbosity.
        """
        #self.swarm.log(self.worker_uuid, message, level)
