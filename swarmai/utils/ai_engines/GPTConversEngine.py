import os
import openai
import tiktoken

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
        self.tiktoken_encoding = tiktoken.encoding_for_model(model_name)

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
        
        total_len = 0
        for message in conversation:
            if "role" not in message:
                raise ValueError("Conversation messages must have a format: {'role': 'user', 'content': 'message'}. 'role' is missing.")
            if "content" not in message:
                raise ValueError("Conversation messages must have a format: {'role': 'user', 'content': 'message'}. 'content' is missing.")
            message["content"] = self.truncate_message(message["content"], self.max_input_length()-total_len-100)
            new_message_len = len(self.tiktoken_encoding.encode(message["content"]))
            total_len += new_message_len
        
        try:
            response = openai.ChatCompletion.create(model=self.model_name, messages=conversation, max_tokens=max_tokens, temperature=temperature, n=1)
        except:
            return ""
        return response["choices"][0]["message"]["content"]

        
        