import os
import openai
import tiktoken

from swarmai.utils.ai_engines.EngineBase import EngineBase
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.llms import OpenAI

from langchain.utilities import GoogleSearchAPIWrapper

class LanchainGoogleEngine(EngineBase):
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

        self.agent = self._init_chain()
        self.search = GoogleSearchAPIWrapper()

    def _init_chain(self):
        """Instantiates langchain chain with all the necessary tools
        """
        llm = OpenAI(temperature=self.temperature)
        tools = load_tools(["google-search", "google-search-results-json"], llm=llm)
        agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=False, return_intermediate_steps=True)
        return agent

    def call_model(self, conversation: list) -> str:
        """Does the search itself but provides very short answers!
        """
        if isinstance(conversation, list):
            prompt = self._convert_conversation_to_str(conversation)
        else:
            prompt = conversation

        response = self.agent(prompt)
        final_response = ""
        intermediate_steps = response["intermediate_steps"]
        for step in intermediate_steps:
            final_response += step[0].log + "\n" + step[1]
        final_response += response["output"]
        return final_response
    
    def google_query(self, query: str) -> str:
        """Does the search itself but provides very short answers!
        """
        response = self.search.run(query)
        return response
    
    def search_sources(self, query: str, n=5):
        """Does the search itself but provides very short answers!
        """
        response = self.search.results(query, n)
        return response
    
    def _convert_conversation_to_str(self, conversation):
        """Converts conversation to a string
        """
        prompt = ""
        for message in conversation:
            prompt += message["content"] + "\n"
        return prompt
    