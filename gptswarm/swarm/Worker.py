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
        self.incoming_messages = [] # lsit of strings! not dicts!
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

class TestWorker(WorkerBase):
    """This class is implementing a test worker.
    """

    def __init__(self, worker_uuid, swarm, gloabl_task: str, **args):
        model_name = "gpt-3.5-turbo"
        default_agent_parameters = {
            "model_name": f"openai/{model_name}",
            "model_params" : {
                "model_name": model_name,
                "temperature": 0.5,
                "max_tokens": 500
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
            self.config_prompt_compute = "You must provide a solution to a given task."

            if len(self.incoming_messages) > 0:
                additional_info =(
                    f"Other workers before you have provided the following solutions to the global task {self.global_task} and their work was evaluated."
                    "Incorpoprate their learnings if needed and maximize the score of your solution. \n\n"
                )
                additional_info += "\n\n".join(self.incoming_messages)

                self.config_prompt_compute += f"\n\n{additional_info}"

            self.conversation = [{"role": "system", "content": self.config_prompt_compute}, {"role": "system", "content": self.global_task}]

            response = self.agent.call_model(self.conversation)
            self.result = {"role": "assistant", "content": response}

            # self-evaluating the result
            self.result_score, self.evaluation = self._self_evaluate()

        elif cycle_type == "share":
            self.share()

    def share(self):
        """Puts the results of the computation into the incoming_messages container of the neighbours.
        Shares both the result and the evaluation.
        """
        print(f"Worker {self.worker_uuid} is sharing the results of the computation.")

        # there can be a change of location in the swarm
        self.neighbours = self.swarm.get_neighbours(self.worker_uuid)

        for neighbour in self.neighbours:
            neighbour.add_message(self.result, self.evaluation)

        self.swarm.add_to_shared_memory(self.result_score, self.result, self.evaluation)

    def _self_evaluate(self):
        """Evaluates the result of the computation.
        """
        self.eval_config_prompt = (
            "Act as a grading bot. Based on the gloabl task, estimate how bad the result solves the task in 5-10 sentences. Take into account that your knowledge is limited and the solution that seems correct is most likely wrong. Help the person improve the solution."
            "Look for potential mistakes or areas of improvement, and pose thought-provoking questions. At the end, evaluate the solution on a scale from 0 to 1 and enclose the score in [[ ]]. \n\n"
            "Task: Write an egaging story about a cat in two sentences. \n Result: The cat was hungry. The cat was hungry. \n Evaluation: The solution does not meet the requirements of the task. The instructions clearly state that the solution should be a story, consisting of two sentences, about a cat that is engaging. To improve your solution, you could consider the following: Develop a clear plot that revolves around a cat and incorporates elements that are unique and interesting. Use descriptive language that creates a vivid picture of the cat and its environment. This will help to engage the reader's senses and imagination.Based on the above, I score the solution as [[0]] \n\n"
            "Task: Write a 1 sentence defenition of a tree. \n Result: A tree is a perennial, woody plant with a single, self-supporting trunk, branching into limbs and bearing leaves, which provides habitat, oxygen, and resources to various organisms and ecosystems. \n Evaluation: Perennial and woody plant: The definition correctly identifies a tree as a perennial plant with woody composition. Single, self-supporting trunk: Trees generally have a single, self-supporting trunk, but there are instances of multi-trunked trees as well. This aspect of the definition could be improved. Provides habitat, oxygen, and resources to various organisms and ecosystems: While true, this part of the definition is focused on the ecological role of trees rather than their inherent characteristics. A more concise definition would focus on the features that distinguish a tree from other plants.  How can the definition be more concise and focused on the intrinsic characteristics of a tree? Can multi-trunked trees be better addressed in the definition? Are there other essential characteristics of a tree that should be included in the definition? Considering the analysis and the thought-provoking questions, I would evaluate the solution as follows: [[0.7]] \n\n"
        )

        self.eval_prompt = f"Task: {self.global_task} \n Result: {self.result['content']} \n Evaluation: \n\n"
        
        self.conversation = [{"role": "system", "content": self.eval_config_prompt}, {"role": "user", "content": self.eval_prompt}]
        evaluation = self.agent.call_model(self.conversation)
        
        try:
            score = float(evaluation.split("[[")[1].split("]]")[0])
        except:
            score = 0

        return score, evaluation


    

    

    