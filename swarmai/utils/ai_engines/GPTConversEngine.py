import os
import openai

from swarmai.utils.ai_engines.EngineBase import EngineBase

class GPTConversEngine(EngineBase):
    """
    gpt-4, gpt-4-0314, gpt-4-32k, gpt-4-32k-0314, gpt-3.5-turbo, gpt-3.5-turbo-0301
    """
    SUPPORTED_MODELS = [
        "gpt-4",
        "gpt-4-0314",
        "gpt-4-32k",
        "gpt-4-32k-0314",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-0301"
    ]

    def __init__(self, model_name: str, temperature: float, max_response_tokens: int):

        if model_name not in self.SUPPORTED_MODELS:
            raise ValueError(f"Model {model_name} is not supported. Supported models are: {self.SUPPORTED_MODELS}")

        super().__init__("openai", model_name, temperature, max_response_tokens)
        
        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OPENAI_API_KEY environment variable is not set.")
        
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def call_model(self, conversation, max_tokens=None, temperature=None) -> str:
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
            raise ValueError("Conversation must have at least one message of format: [{'role': 'user', 'content': 'message'}]")
        
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
    
    def _truncate_message(self, message, max_tokens):
        """Truncate a message to a maximum number of tokens.
        We use a rule of thumb that 1 token is about 3 symbols (https://platform.openai.com/tokenizer)
        TODO: use tiktoken

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
        