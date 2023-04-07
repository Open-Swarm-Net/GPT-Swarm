import sys
import os
import openai

from gptswarm.utils.LLMCaller import LLMCaller

class GPTCaller(LLMCaller):
    """This class is responsible for interacting with the openai API.
    model_parameters = {"model_name": name}

    Potential names: https://platform.openai.com/docs/models/overview
    """
    CONVERSTATIONAL_MODELS = [
        "gpt-4", "gpt-4-0314", "gpt-4-32k", "gpt-4-32k-0314",
        "gpt-3.5-turbo", "gpt-3.5-turbo-0301",
        ]

    def __init__(self, model_parameters):
        super().__init__(model_parameters)
        
        # check if configuration is valid
        if "model_name" not in model_parameters:
            raise Exception("model_name is not in model_parameters")
        if "OPENAI_API_KEY" not in os.environ:
            raise Exception("OPENAI_API_KEY is not in os.environ")

        self.model_name = model_parameters["model_name"]
        openai.api_key = os.getenv("OPENAI_API_KEY")

        ## check is openai api key is set and openai api is working
        try:
            models = openai.Model.list()
            print(f"OpenAI connection successful! Model: {self.model_name}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    def call_model(self, conversation, call_parameters):
        """Calls the LLM with the given conversation and input format.

        Args:
            conversation (list[dict]): The conversation to be completed. Example:
                [
                    {"role": "system", "content": configuration_prompt},
                    {"role": "user", "content": prompt}
                ]

            call_parameters (dict): The parameters for the call specific for each provider. Example:
                {"max_tokens": 100, "temperature": 0.5, "n": 1, "stop": None}
        """
        # convert conversation to openai format
        conversation, call_parameters = self._convert_to_correct_format(conversation, call_parameters)

        # call openai api
        response = self.gen_request_to_api(conversation, **call_parameters)
        return response
    
    def _convert_to_correct_format(self, conversation, call_parameters):
        if self.model_name in self.CONVERSTATIONAL_MODELS:
            # already in the gpt-3.5-turbo format
            return conversation, call_parameters
        else:
            # convert to string
            conversation = self._convert_to_string(conversation)
            return conversation, call_parameters

    def gen_request_to_api(self, messages, max_tokens=100, temperature=0.5, n=1, stop=None):
        if self.model_name in self.CONVERSTATIONAL_MODELS:
            response = openai.ChatCompletion.create(model=self.model_name, messages=messages, max_tokens=max_tokens, temperature=temperature, n=n, stop=stop)
            return response["choices"][0]["message"]["content"]
        else:
            # idk who'd like to use the old gpt-3, but just in case
            response = openai.Completion.create(model=self.model_name, prompt=messages, max_tokens=max_tokens, temperature=temperature, n=n, stop=stop)
            return response["choices"][0]["text"]

        