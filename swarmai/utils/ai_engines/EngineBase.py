from abc import ABC, abstractmethod

class EngineBase(ABC):
    """Abstract base class for the AI engines.
    Engines define the API for the AI engines that can be used in the swarm.
    """
    def __init__(self, provider, model_name: str, temperature: float, max_response_tokens: int):
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        self.max_response_tokens = max_response_tokens

    @abstractmethod
    def call_model(self, conversation: list) -> str:
        """Call the model with the given conversation.
        Input always in the format of openai's conversation.
        Output a string.

        Args:
            conversation (list[dict]): The conversation to be completed. Example:
                [
                    {"role": "system", "content": configuration_prompt},
                    {"role": "user", "content": prompt}
                ]

        Returns:
            str: The response from the model.
        """
        raise NotImplementedError

    @abstractmethod
    def max_input_length(self) -> int:
        """Returns the maximum length of the input to the model.

        Returns:
            int: The maximum length of the input to the model.
        """
        raise NotImplementedError
    
    @abstractmethod
    def truncate_message(self, message):
        """Truncates the message using tiktoken"""
        raise NotImplementedError