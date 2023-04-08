import sys
import os
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

from langchain.utilities import GoogleSearchAPIWrapper

from gptswarm.utils.LLMAgentBase import LLMAgentBase

class LangchainAgent(LLMAgentBase):
    """This class is implementing a langchain agent.
    It's similar to a pure GPT agent, but can use differnet integrations.
    For now it supports only the OpenAI for LLMs.

    https://python.langchain.com/en/stable/getting_started/getting_started.html
    https://github.com/gkamradt/langchain-tutorials/blob/main/agents/Agents.ipynb
    """

    def __init__(self, agent_parameters):
        """The langchain agent can have the following parameters:
        agent_parameters = {
            "chat": True,
            "model_name": "langchain/gpt-3.5-turbo",
            "tools": ['serpapi', 'wolfram-alpha'],
            "model_params": {
                "model_name": "gpt-3.5-turbo",
                "temperature": 0.5,
                "max_tokens": 400
                },
            "agent": "zero-shot-react-description",
            }
        """
        super().__init__(agent_parameters)
        self.agent_parameters = agent_parameters
        self.isChat = agent_parameters["chat"]

        tools = load_tools(agent_parameters["tools"])
        if agent_parameters["chat"]:
            llm = ChatOpenAI(**agent_parameters["model_params"])
        else:
            llm = OpenAI(**agent_parameters["model_params"])

        self.agent = initialize_agent(tools, llm, agent=agent_parameters["agent"], verbose=True)

        ## check is openai api key is set and openai api is working
        try:
            _ = self.agent.run("What is a house?")
            print(f"Langchain agent is working! Model: {self.agent}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    def validate_integration_keys(self):
        if "OPENAI_API_KEY" not in os.environ:
            raise Exception("OPENAI_API_KEY is not in os.environ")
        if "google-search" in self.agent_parameters["tools"]:
            if "GOOGLE_API_KEY" not in os.environ:
                raise Exception("GOOGLE_API_KEY is not in os.environ")
            if "CUSTOM_SEARCH_ENGINE_ID" not in os.environ:
                raise Exception("CUSTOM_SEARCH_ENGINE_ID is not in os.environ")

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
        response = self.gen_request_to_api(conversation)
        return response
    
    def _convert_to_correct_format(self, conversation, call_parameters):
        if self.isChat:
            # converting openai format to langchain format for langchain to convert back to openai format =))))
            messages = []
            for turn in conversation:
                if turn["role"] == "system":
                    messages.append(SystemMessage(content=turn["content"]))
                elif turn["role"] == "user":
                    messages.append(HumanMessage(content=turn["content"]))
                elif turn["role"] == "assistant":
                    messages.append(AIMessage(content=turn["content"]))
                else:
                    raise ValueError(f"role must be system or user. got {turn['role']}")
            return messages, call_parameters
        else:
            # convert to string
            conversation = self._convert_to_string(conversation)
            return conversation, call_parameters

    def gen_request_to_api(self, messages):
        if self.isChat:
            return self.agent.run(messages)
        else:
            if not isinstance(messages, str):
                raise ValueError(f"messages must be a string. got {type(messages)}")
            return self.agent.run(messages)