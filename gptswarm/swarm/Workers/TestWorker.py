from gptswarm.swarm.Workers.WorkerBase import WorkerBase

class TestWorker(WorkerBase):
    """This class is implementing a test worker.
    """

    def __init__(self, worker_uuid, swarm, challenge):
        """A general purpose worker that can be used for testing.

        Args:
            worker_uuid (uuid): a unique identifier for the worker
            swarm (Swarm): the swarm that the worker belongs to
            challenge (Implementation of ChallengeBase): a challenge that the worker will solve, has methods get_problem and evaluate_solution
        """
        model_name = "gpt-3.5-turbo"
        default_agent_parameters = {
            "model_name": f"openai/{model_name}",
            "model_params" : {
                "model_name": model_name,
                "temperature": 0.5,
                "max_tokens": 500
                }
            }
        super().__init__(worker_uuid, swarm, challenge)

        # implementing additional stuff
        self.agent = self.AGENT_TYPES["gpt"](default_agent_parameters)

    def perform_task(self, cycle_type):
        """Performs a task for the given cycle type.
        """
        print(f"Worker {self.worker_uuid} is performing a task for the {cycle_type} cycle.")
        if cycle_type == "compute":
            self.config_prompt_compute = ""

            if len(self.incoming_messages) > 0:
                additional_info =(
                    f"Other workers before you have provided the following solutions to the global task and their work was tested."
                    "Incorpoprate the learnings if needed and improve the score. \n\n"
                )
                additional_info += "\n\n".join(self.incoming_messages)

                self.config_prompt_compute += f"\n\n{additional_info}"

            self.conversation = [{"role": "system", "content": self.config_prompt_compute}, {"role": "user", "content": self.global_task}]

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
        Normal workers should test the solution using the challenge's evaluate_solution method.
        Some workers in the future can perform self-evaluation.
        """

        # self.eval_config_prompt = (
        #     "Act as a grading bot. Based on the gloabl task, estimate how bad the result solves the task in 5-10 sentences. Take into account that your knowledge is limited and the solution that seems correct is most likely wrong. Help the person improve the solution."
        #     "Look for potential mistakes or areas of improvement, and pose thought-provoking questions. At the end, evaluate the solution on a scale from 0 to 1 and enclose the score in [[ ]]. \n\n"
        #     "Task: Write an egaging story about a cat in two sentences. \n Result: The cat was hungry. The cat was hungry. \n Evaluation: The solution does not meet the requirements of the task. The instructions clearly state that the solution should be a story, consisting of two sentences, about a cat that is engaging. To improve your solution, you could consider the following: Develop a clear plot that revolves around a cat and incorporates elements that are unique and interesting. Use descriptive language that creates a vivid picture of the cat and its environment. This will help to engage the reader's senses and imagination.Based on the above, I score the solution as [[0]] \n\n"
        #     "Task: Write a 1 sentence defenition of a tree. \n Result: A tree is a perennial, woody plant with a single, self-supporting trunk, branching into limbs and bearing leaves, which provides habitat, oxygen, and resources to various organisms and ecosystems. \n Evaluation: Perennial and woody plant: The definition correctly identifies a tree as a perennial plant with woody composition. Single, self-supporting trunk: Trees generally have a single, self-supporting trunk, but there are instances of multi-trunked trees as well. This aspect of the definition could be improved. Provides habitat, oxygen, and resources to various organisms and ecosystems: While true, this part of the definition is focused on the ecological role of trees rather than their inherent characteristics. A more concise definition would focus on the features that distinguish a tree from other plants.  How can the definition be more concise and focused on the intrinsic characteristics of a tree? Can multi-trunked trees be better addressed in the definition? Are there other essential characteristics of a tree that should be included in the definition? Considering the analysis and the thought-provoking questions, I would evaluate the solution as follows: [[0.7]] \n\n"
        # )

        # self.eval_prompt = f"Task: {self.global_task} \n Result: {self.result['content']} \n Evaluation: \n\n"
        
        # self.conversation = [{"role": "system", "content": self.eval_config_prompt}, {"role": "user", "content": self.eval_prompt}]
        # evaluation = self.agent.call_model(self.conversation)
        
        # try:
        #     score = float(evaluation.split("[[")[1].split("]]")[0])
        # except:
        #     score = 0

        score, evaluation = self.challenge.evaluate_solution(self.result["content"], num_test_cases=100)

        return score, evaluation
