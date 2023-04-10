from abc import ABC, abstractmethod

from gptswarm.utils.GPTAgent import GPTAgent
from gptswarm.utils.LangchainAgent import LangchainAgent

class WorkerBase(ABC):
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
        self.worker_type = "abstract"

        # getting the challenge
        self.challenge = challenge
        self.global_task = self.challenge.get_problem()

        # getting the list of neighbours: [worker_obj, worker_obj, ...]
        self.neighbours = [] # at the init stage the neighbours are not known

        # defining containers for the data
        # expected form of the conversation: [{"role": "user", "content": str}, {"role": "assistant", "content": str}, ...]
        self.conversation = []
        self.incoming_messages = [] # lsit of tuple (result_score, result, evaluation)
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

    def add_message(self, result_score, result, evaluation):
        """Receives a message from another worker.
        """
        if isinstance(result, dict):
            result = result["content"]
        if isinstance(evaluation, dict):
            evaluation = evaluation["content"]

        self.incoming_messages.append((result_score, result, evaluation))

    def log(self, message, level="info"):
        """Logs a message. The swarm handles the logging and verbosity.
        """
        self.swarm.log(agent=self.worker_type, message=message, level=level)

    def truncate_message(self, message, max_tokens):
        """Truncate a message to a maximum number of tokens.
        We use a rule of thumb that 1 token is about 3 symbols (https://platform.openai.com/tokenizer)

        Args:
            message (str):
            max_tokens (int): 

        Returns:
            str: truncated message
        """
        
        # count words
        symbol_count = len(message)
        conversion_factor = 3

        if symbol_count <= max_tokens*conversion_factor:
            return message

        new_len = int(max_tokens*conversion_factor)
        self.log(f"Truncating message from {symbol_count} to {new_len} symbols", level="debug")
        return message[:new_len]
