import os
import openai

from swarmai.agents.AgentBase import AgentBase
from swarmai.utils.memory.DictInternalMemory import DictInternalMemory

class GPTAgent(AgentBase):
    """Class that uses conversational GPT models of OpenAI to perform the task.
    
    - Agents are the entities that perform the task in the swarm.
    - Agents can have different roles and implementations, but they all need to implement a set of methods that would allow them to work together in a swarm.
    - Implements the threading. Thread class to allow the swarm to run in parallel.
    """

    def __init__(self, agent_id, agent_role, swarm, shared_memory, challenge, logger):
        """Initialize the agent.
        
        Args:
            agent_role (str): The type of the agent, ex. worker, explorer, evaluator, etc.
            swarm (Swarm): The swarm object.
            shared_memory (SharedMemoryBase implementation): The shared memory object.
            neighbor_queues (lsit): The queues to communicate with the neighbors.
            challenge (Challenge implementation): The challenge object.
            logger (Logger): The logger object.
        """
        super().__init__(agent_id, agent_role, swarm, shared_memory, challenge, logger)

        # some mandatory components
        self.internal_memory = DictInternalMemory(4)

        # configuring engine
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = "gpt-3.5-turbo"
        self.max_response_tokens = 1500
        self.temperature = 0.5

        # some other parameters
        self.result = ''
        self.result_score = 0
        self.evaluation = ''

    def perform_task(self):
        """main method of the agent that defines the task it performs.
        Executed in the abstract class.
        """
        cycle_prompt = ''

        self.logger.info(f"Agent {self.agent_id} is performing the task")
        role_prompt = f"Act as a professional {self.agent_role}.\n"
        cycle_prompt += role_prompt

        # first, we summarize the incoming messages from the internal memory
        incomming_summary = self._summarize_incoming_messages()
        if incomming_summary:
            cycle_prompt += incomming_summary
            cycle_prompt += "Now, improve the solution."

        # then make the model generate a new solution
        conversation = [
            {"role": "system", "content": cycle_prompt},
            {"role": "user", "content": self.global_task}
        ]

        result = self.call_model(conversation)
        self.result = result

        # evaluate the result
        self.result_score, self.evaluation = self._self_evaluate()

        self.logger.info(f"Agent: {self.agent_id} finished; Score: {self.result_score:.2f}")

    def share(self):
        """Main method of the agent that defines how it shares its results with the neighbors.
        Executed in the abstract class.
        """
        pass
        #self._send_data_to_neighbors({"score": self.result_score, "content": self.result + "\n" + self.evaluation})
    
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
        self.logger.debug(f"Truncating message from {symbol_count} to {new_len} symbols", level="debug")
        return message[:new_len]

    def call_model(self, conversation, max_tokens=None, temperature=None):
        """Calls the gpt-3.5 or gpt-4 model to generate a response to a conversation.

        Args:
            conversation (list[dict]): The conversation to be completed. Example:
                [
                    {"role": "system", "content": configuration_prompt},
                    {"role": "user", "content": prompt}
                ]
        """
        if max_tokens is None:
            max_tokens = self.max_response_tokens
        if temperature is None:
            temperature = self.temperature

        if isinstance(conversation, str):
            conversation = [{"role": "user", "content": conversation}]

        if len(conversation) == 0:
            raise ValueError("Conversation must have at least one message of format: {'role': 'user', 'content': 'message'}")
        
        for message in conversation:
            if "role" not in message:
                raise ValueError("Conversation messages must have a format: {'role': 'user', 'content': 'message'}. 'role' is missing.")
            if "content" not in message:
                raise ValueError("Conversation messages must have a format: {'role': 'user', 'content': 'message'}. 'content' is missing.")
            
        response = openai.ChatCompletion.create(model=self.model_name, messages=conversation, max_tokens=max_tokens, temperature=temperature, n=1)
        return response["choices"][0]["message"]["content"]
    
    def _self_evaluate(self):
        """Evaluates the result of the computation.
        Normal workers should test the solution using the challenge's evaluate_solution method.
        Some workers in the future can perform self-evaluation.
        """
        try:
            score, evaluation = self.challenge.evaluate_solution(self.result, num_test_cases=2000)
        except Exception as e:
            self.logger.info(f"Agent {self.agent_id} failed to run the solution.")
            self.logger.error(e)
            self.evaluation = f"Final score is 0. The submitted solution failed to run. Avoid following errors: {e}"
            self.result_score = 0
        
        evaluation = self._evaluation_compression(self.result, evaluation)

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
        response = self.call_model(conversation_compression)

        self.logger.debug(f"Condencing the evaluation for the worker {self.agent_id}. \n\n Conent: {content_prompt} \n\n Compression: {response}")
        return response

    def _summarize_incoming_messages(self):
        """Summarizes the incoming messages. They are stored in the self.internal_memory as a dict {"score": score, "content": content}
        """
        config_prompt_summarisation = (
            f"Act as a professional {self.agent_role} that gives feedback. Be extremely critical, concise, constructive and specific."
            "You will be presented with a problem and a set of solutions and learnings other people have shared with you."
            "First, briefly summarize the best solution in less than 5 sentences focusing on the main ideas, key operations or building blocks, and performance metrics."
            "Then, summarize all the learnings into at most 5 sentences to guide the person to improve the solution further and achieve the highest score. Include examples if possible."
        )

        if self.internal_memory.len() > 0:
            best_solution = self.internal_memory.get_top_n(n=1)

            learnings = [x["content"] for x in self.internal_memory]
            learnings = "\n\n".join(learnings)

            content_prompt = f"Best potential solution so far:\n{best_solution} \n\n Learnings: \n{learnings} \n\n"
            content_prompt = self.truncate_message(content_prompt, 4097-self.max_response_tokens)

            conversation = [{"role": "system", "content": config_prompt_summarisation}, {"role": "user", "content": content_prompt}]

            response = self.call_model(conversation)            
            self.logger.debug(f"Condencing the incoming messages. \n\n Conent: {content_prompt} \n\n Compression: {response}")
        else:
            self.logger.debug(f"No incoming messages to summarize.")
            response = None

        return response
        