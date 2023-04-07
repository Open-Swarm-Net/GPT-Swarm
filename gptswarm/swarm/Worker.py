from gptswarm.utils.OpenAICaller import OpenAICaller

class Worker:
    """The worker class is a single entity in the swarm that performs different taks.
    Currently the worker is based on the openai API for simplicity, but abstractions and extentions are welcome.
    """
