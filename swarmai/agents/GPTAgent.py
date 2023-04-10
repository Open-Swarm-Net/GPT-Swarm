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
        """main method of the agent that defines the task it performs
        """
        self.logger.info(f"Agent {self.agent_id} is performing the task")
        role_prompt = f"Act as a professional {self.agent_role}.\n"
        configuration_prompt = ""

        conversation = [
            {"role": "system", "content": role_prompt+configuration_prompt},
            {"role": "user", "content": self.global_task}
        ]

        result = self.call_model(conversation)
        self.result = result
        self.result_score = 0.5 
        

    def share(self):
        """Main method of the agent that defines how it shares its results with the neighbors
        """
        self._send_data_to_neighbors({"score": self.result_score, "content": self.result + "\n" + self.evaluation})
    
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
        