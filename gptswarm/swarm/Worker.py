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

    def __init__(self, worker_uuid, swarm, agent_type, agent_parameters):
        self.worker_uuid = worker_uuid
        self.swarm = swarm
        self.agent_type = agent_type
        self.agent_parameters = agent_parameters

        # getting the list of neighbours: [worker_obj, worker_obj, ...]
        self.neighbours = [] # at the init stage the neighbours are not known

        # defining containers for the data
        # expected form of the conversation: [{"role": "user", "content": str}, {"role": "assistant", "content": str}, ...]
        self.conversation = []
        self.incoming_messages = []
        self.result = {"role": "assistant", "content": ""}
        self.result_score = 0

    @abstractmethod
    def perform_task(self, cycle_type):
        pass

    @abstractmethod
    def share(self):
        pass

    @abstractmethod
    def _self_evaluate(self):
        pass

    def add_message(self, message):
        """Receives a message from another worker.
        """
        self.incoming_messages.append(message)


class TestWorker(WorkerBase):
    """This class is implementing a test worker.
    """

    def __init__(self, worker_uuid, swarm, gloabl_task: str, **args):
        model_name = "gpt-3.5-turbo"
        default_agent_parameters = {
            "model_name": f"openai/{model_name}",
            "model_params" : {
                "model_name": model_name,
                "temperature": 0.7,
                "max_tokens": 400
                }
            }
        super().__init__(worker_uuid, swarm, "gpt", default_agent_parameters)
        self.agent = self.AGENT_TYPES["gpt"](default_agent_parameters)

        self.global_task = gloabl_task

    def perform_task(self, cycle_type):
        """Performs a task for the given cycle type.
        """
        print(f"Worker {self.worker_uuid} is performing a task for the {cycle_type} cycle.")
        if cycle_type == "compute":
            self.conversation = [{"role": "system", "content": self.global_task}] + self.incoming_messages
            response = self.agent.call_model(self.conversation)
            self.result = {"role": "assistant", "content": response}
        elif cycle_type == "share":
            self.result_score = self._self_evaluate()
            self.share()

    def share(self):
        """Puts the results of the computation into the incoming_messages container of the neighbours.
        Also can add to the shared memory
        """
        print(f"Worker {self.worker_uuid} is sharing the results of the computation.")

        # there can be a change of location in the swarm
        self.neighbours = self.swarm.get_neighbours(self.worker_uuid)
        self.result_score = self._self_evaluate()

        for neighbour in self.neighbours:
            neighbour.add_message(self.result)

        self.swarm.add_to_shared_memory(self.result_score, self.result)

    def _self_evaluate(self):
        """Evaluates the result of the computation.
        """
        self.eval_rpompt = (
            "Act as a grading bot. Base on the gloabl task, estimate how well the result solves the task on a scale from 0 to 1. Enclose the score in [[ ]]. \n\n"
            "\n Task: Write a story about a cat. \n Result: The cat was hungry. The cat was hungry. \n Score: [[0.2]] \n\n"
            "Task: Write a story about a cat. \n Result: The cat was hungry. It ate a mouse. \n Score: [[0.4]] \n\n"
            f"Task: {self.global_task} \n Result: {self.result['content']} \n Score: \n\n"
        )
        
        self.conversation = [{"role": "user", "content": self.eval_rpompt}]
        response = self.agent.call_model(self.conversation)
        
        try:
            score = float(response.split("[[")[1].split("]]")[0])
        except:
            score = 0

        return score


    

    

    