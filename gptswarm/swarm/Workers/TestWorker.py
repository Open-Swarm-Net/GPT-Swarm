from gptswarm.swarm.Workers.WorkerBase import WorkerBase
import numpy as np

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
        self.default_agent_parameters = {
            "model_name": f"openai/{model_name}",
            "model_params" : {
                "model_name": model_name,
                "temperature": 0.1,
                "max_tokens": 1500
                }
            }
        super().__init__(worker_uuid, swarm, challenge)

        # implementing additional stuff
        self.agent = self.AGENT_TYPES["gpt"](self.default_agent_parameters)
        self.worker_type = "test_worker"

    def perform_task(self, cycle_type):
        """Performs a task for the given cycle type.
        """
        if cycle_type == "compute":
            self.config_prompt_compute = "Act as a professional python developer."

            incomming_summary = self._summarize_incoming_messages()
            if incomming_summary:
                self.config_prompt_compute += incomming_summary
                self.config_prompt_compute += "Now, try to improve the solution."

            self.conversation = [{"role": "system", "content": self.config_prompt_compute}, {"role": "user", "content": self.global_task}]

            response = self.agent.call_model(self.conversation)
            self.result = {"role": "assistant", "content": response}
            
            self.log(f"Performing a task for the {cycle_type} cycle.\n\n Config prompt: {self.config_prompt_compute}. \n\n Result: {self.result}", level="debug")

            # self-evaluating the result
            self.result_score, self.evaluation = self._self_evaluate()

        elif cycle_type == "share":
            self.share()

    def share(self):
        """Puts the results of the computation into the incoming_messages container of the neighbours.
        Shares both the result and the evaluation.
        """
        # there can be a change of location in the swarm
        self.neighbours = self.swarm.get_neighbours(self.worker_uuid)
        
        # prepend self to the self.neighbours, which is an np array
        self.neighbours = np.append(np.array([self]), self.neighbours)

        for neighbour in self.neighbours:
            neighbour.add_message(self.result_score, self.result, self.evaluation)

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
        try:
            score, evaluation = self.challenge.evaluate_solution(self.result["content"], num_test_cases=2000)
        except Exception as e:
            self.log(f"Failed to perform task")
            self.log(e, level="error")
            self.evaluation = f"Final score is 0. The submitted solution failed to run. Avoid following errors: {e}"
            self.result_score = 0
            raise e
        evaluation = self._evaluation_compression(self.result["content"], evaluation)

        self.log(f"Worker: {self.worker_uuid}; Score: {score:.2f}")

        return score, evaluation
    
    def _evaluation_compression(self, solution, evaluation):
        """Because the models have a limited number of tokens, the evaluation has to be compressed before sharing with the neighbours.
        """
        configuration_prompt_compression = (
            "Act as a professional software engineer and python developer that gives feedback. Be extremely critical, concise, constructive and specific."
            "You will be presented with a problem, candidate solution and evaluation."
            "First, briefly summarize the solution in less than 5 sentences focusing on the main idea of the algorithm and including key operations or building blocks or the core idea behind the algorithm, and performance metrics."
            "Thenextract the most important information from the solution and evaluation and condence it into at most 5 sentences to guide the developer to improve the solution and achieve the higest score."
            "Look for potential mistakes or areas of improvement based on the evaluation, pose thought-provoking questions and important learnings. Include examples if possible."
        )

        content_prompt = f"Problem: {self.global_task} \n Solution: {solution} \n Evaluation: {evaluation} \n\n"

        conversation_compression = [{"role": "system", "content": configuration_prompt_compression}, {"role": "user", "content": content_prompt}]
        response = self.agent.call_model(conversation_compression)

        self.log(f"Condencing the evaluation for the worker {self.worker_uuid}. \n\n Conent: {content_prompt} \n\n Compression: {response}", level="debug")
        return response
    
    def _summarize_incoming_messages(self):
        """Summarizes the incoming messages.
        """
        config_prompt_summarisation = (
            "Act as a professional software engineer and python developer that gives feedback. Be extremely critical, concise, constructive and specific."
            "You will be presented with a problem and a set of solutions and learnings other developers have shared with you."
            "First, briefly summarize the best solution in less than 5 sentences focusing on the main idea of the algorithm and including key operations or building blocks or the core idea behind the algorithm, and performance metrics."
            "Then, summarize all the learnings into at most 5 sentences to guide the developer to improve the solution further and achieve the highest score. Include examples if possible."
        )

        if len(self.incoming_messages) > 0:
            # first, select top 4 of the best incomding messages. self.incoming_messages=list(tuple(result_score, result, evaluation))
            self.incoming_messages = sorted(self.incoming_messages, key=lambda x: x[0], reverse=True)
            self.incoming_messages = self.incoming_messages[:min(4, len(self.incoming_messages))]

            best_solution = self.incoming_messages[0][1]

            learnings = [x[2] for x in self.incoming_messages]
            learnings = "\n\n".join(learnings)

            content_prompt = f"Best potential solution so far:\n{best_solution} \n\n Learnings: \n{learnings} \n\n"
            content_prompt = self.truncate_message(content_prompt, 4097-self.default_agent_parameters["model_params"]["max_tokens"])

            conversation = [{"role": "system", "content": config_prompt_summarisation}, {"role": "user", "content": content_prompt}]

            response = self.agent.call_model(conversation)            
            self.log(f"Condencing the incoming messages. \n\n Conent: {content_prompt} \n\n Compression: {response}", level="debug")
        else:
            self.log(f"No incoming messages to summarize.", level="debug")
            response = None

        return response



class ExplorerWorker(TestWorker):
    def __init__(self, worker_uuid, swarm, challenge):
        super().__init__(worker_uuid, swarm, challenge)
        model_name = "gpt-3.5-turbo"
        self.default_agent_parameters = {
            "model_name": f"openai/{model_name}",
            "model_params" : {
                "model_name": model_name,
                "temperature": 0.8,
                "max_tokens": 1500
                }
            }

        # implementing additional stuff
        self.agent = self.AGENT_TYPES["gpt"](self.default_agent_parameters)
        self.worker_type = "worker_explorer"