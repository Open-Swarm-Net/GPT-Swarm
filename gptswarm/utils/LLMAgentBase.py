from abc import ABC, abstractmethod

class LLMAgentBase:
    """Abstract class that defines the interface for the models caller.
    Has methods to call the models for example though the api.
    As input it can take models parameters like temperature, as well as the conversation list in the openAI style.
    If the conversation style is not supported by the model, it will be converted to the string.

    I did it in an abstract way, in case we want to add more models in the future.
    """
    def __init__(self, agent_parameters=None):
        """Models parameters defines the configuration of the model.
        Example: 
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
        self.model_parameters = agent_parameters if agent_parameters else {}

    @abstractmethod
    def call_model(self, conversation):
        """
        Calls the LLM with the given conversation and input format.

        Args:
            conversation (list[dict]): The conversation to be completed. Example:
                [
                    {"role": "system", "content": configuration_prompt},
                    {"role": "user", "content": prompt}
                ]
        """
        pass

    @abstractmethod
    def _convert_to_correct_format(self, conversatin):
        pass
    
    def _convert_to_string(self, conversation):
        """Some models don't support conversations like openAI, so we convert it to a single string.
        """
        conversation_str = ''
        for turn in conversation:
            role = turn['role']
            content = turn['content']
            conversation_str += f'{role}: {content}\n'
        return conversation_str.strip()
