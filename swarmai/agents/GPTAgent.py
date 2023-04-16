import os
import openai

from swarmai.agents.AgentBase import AgentBase
from swarmai.utils.memory.DictInternalMemory import DictInternalMemory
from swarmai.utils.PromptFactory import PromptFactory

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
        self.temperature = 0.2

        # some other parameters
        self.result = ''
        self.result_score = 0
        self.evaluation = ''
        self.role_prompt = f"Act as a professional {self.agent_role}.\n"

    def _reset(self):
        """Reset the agent to its initial state.
        """
        self.result = ''
        self.result_score = 0
        self.evaluation = ''

    def perform_task(self):
        """main method of the agent that defines the task it performs.
        Executed in the abstract class.
        """
        self.current_step = "perform_task"
        self._reset()
        cycle_prompt = ''

        self.log(f"Performing the task")
        cycle_prompt += self.role_prompt

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
        self.log(f"Result: {self.result}", level="debug")

        # evaluate the result
        self.result_score, self.evaluation = self._self_evaluate()

        self.log(f"Finished; Score: {self.result_score:.2f}")

    def share(self):
        """Main method of the agent that defines how it shares its results with the neighbors.
        Executed in the abstract class.
        """
        self.current_step = "share"
        if self.result_score > 0:
            self._send_data_to_neighbors({"score": self.result_score, "content": f"*Potential solution:*\n{self.result} \n\n*Evaluation:*\n{self.evaluation}"})
            #self._send_data_to_swarm({"score": self.result_score, "content": f"*Potential solution:*\n{self.result} \n\n*Evaluation:*\n{self.evaluation}"})
            #self._send_data_to_neighbors({"score": self.result_score, "content": self.evaluation})
            self._send_data_to_swarm({"score": self.result_score, "content": self.evaluation})
        else:
            self.log("Result score is 0, not sharing the result.")
    
    def truncate_message(self, message, max_tokens):
        """Truncate a message to a maximum number of tokens.
        We use a rule of thumb that 1 token is about 3 symbols (https://platform.openai.com/tokenizer)

        Args:
            message (str):
            max_tokens (int): 

        Returns:
            str: truncated message
        """
        self.current_step = "truncate_message"
        
        # count words
        symbol_count = len(message)
        conversion_factor = 3

        if symbol_count <= max_tokens*conversion_factor:
            return message

        new_len = int(max_tokens*conversion_factor)
        self.log(f"Truncating message from {symbol_count} to {new_len} symbols", level="debug")
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
        self.current_step = "call_model"

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
        
        try:
            response = openai.ChatCompletion.create(model=self.model_name, messages=conversation, max_tokens=max_tokens, temperature=temperature, n=1)
        except:
            return ""
        return response["choices"][0]["message"]["content"]
    
    def _self_evaluate(self):
        """Evaluates the result of the computation.
        Normal workers should test the solution using the challenge's evaluate_solution method.
        Some workers in the future can perform self-evaluation.
        """
        self.current_step = "self_evaluate"
        try:
            score, evaluation = self.challenge.evaluate_solution(self.result, num_test_cases=10000)
        except Exception as e:
            self.log(f"Failed to run the solution.", level="error")
            self.log(e, level="error")
            self.evaluation = f"Final score is 0. The submitted solution failed to run. Avoid following errors: {e}"
            self.result_score = 0
        
        evaluation = self._evaluation_compression(self.result, evaluation)

        return score, evaluation
    
    def _evaluation_compression(self, solution, evaluation):
        """Because the models have a limited number of tokens, the evaluation has to be compressed before sharing with the neighbours.
        """
        self.current_step = "evaluation_compression"
        configuration_prompt = self.role_prompt + PromptFactory.StandardPrompts.single_solution_summarisation
        content_prompt = f"Problem: {self.global_task} \n Solution: {solution} \n Evaluation: {evaluation} \n\n"

        conversation_compression = [{"role": "system", "content": configuration_prompt}, {"role": "user", "content": content_prompt}]
        response = self.call_model(conversation_compression)

        self.log(f"Condencing the evaluation for the worker {self.agent_id}. \n\n *Content*: {content_prompt} \n\n *Compression*: {response}", level="debug")
        return response

    def _summarize_incoming_messages(self):
        """Summarizes the incoming messages. They are stored in the self.internal_memory as a dict {"score": score, "content": content}
        """
        self.current_step = "summarize_incoming"
        config_prompt = self.role_prompt + PromptFactory.StandardPrompts.solutions_summarisation

        if self.internal_memory.len() > 0:
            best_solution = self.internal_memory.get_top_n(n=1)[0][1]
            best_solution = f"*Score:*{best_solution['score']}\n*Content:*\n{best_solution['content']}"

            contents = self.internal_memory.data # dict = {"key": {"score": score, "content": content}, ...}

            learnings = [x["content"].split("\n\n*Evaluation:*\n")[-1] for x in contents.values()]
            learnings = "\n\n".join(learnings)

            content_prompt = f"Best potential solution so far:\n{best_solution} \n\n Learnings: \n{learnings} \n\n"
            content_prompt = self.truncate_message(content_prompt, 4097-self.max_response_tokens)

            conversation = [{"role": "system", "content": config_prompt}, {"role": "user", "content": content_prompt}]

            response = self.call_model(conversation)            
            self.log(f"Condencing the incoming messages. \n\n *Content*: {content_prompt} \n\n *Compression*: {response}", level="debug")
        else:
            self.log(f"No incoming messages to summarize.", level="debug")
            response = None

        return response


class ExplorerGPT(GPTAgent):
    def __init__(self, agent_id, agent_role, swarm, shared_memory, challenge, logger):
        super().__init__(agent_id, agent_role, swarm, shared_memory, challenge, logger)

        self.temperature = 0.5