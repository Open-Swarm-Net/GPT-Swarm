from abc import ABC, abstractmethod

class EngineBase(ABC):
    """Abstract base class for the AI engines.
    Engines define the API for the AI engines that can be used in the swarm.
    """
    
    TOKEN_LIMITS = {
        "gpt-4": 16*1024,
        "gpt-4-0314": 16*1024,
        "gpt-4-32k": 32*1024,
        "gpt-4-32k-0314": 32*1024,
        "gpt-3.5-turbo": 4*1024,
        "gpt-3.5-turbo-0301": 4*1024
    }
    
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
    
        
    def max_input_length(self) -> int:
        """Returns the maximum length of the input to the model in temrs of tokens.

        Returns:
            int: The max tokens to input to the model.
        """
        return self.TOKEN_LIMITS[self.model_name]-self.max_response_tokens
    
    def truncate_message(self, message, token_limit=None):
        """Truncates the message using tiktoken"""
        max_tokens = self.max_input_length()
        message_tokens = self.tiktoken_encoding.encode(message)

        if token_limit is not None:
            max_tokens = min(max_tokens, token_limit)

        if len(message_tokens) <= max_tokens:
            return message
        else:
            return self.tiktoken_encoding.decode(message_tokens[:max_tokens])