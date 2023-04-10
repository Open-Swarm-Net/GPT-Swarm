from abc import ABC, abstractmethod

class InternalMemoryBase(ABC):
    """Abstract base class for internal memory of agents in the swarm.
    """

    def __init__(self, n_entries):
        """Initialize the internal memory. In the current architecture the memory always consists of a set of soltuions or evaluations.
        During the operation, the agent should retrivie best solutions from it's internal memory based on the score.

        Moreover, the project is designed around LLMs for the proof of concepts, so we treat all entry content as a string.
        """
        self.n_entries = n_entries

    @abstractmethod
    def add_entry(self, score, entry):
        """Add an entry to the internal memory.
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_top_n(self, n):
        """Get the top n entries from the internal memory.
        """
        raise NotImplementedError