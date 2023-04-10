import threading

class DictSharedMemory():
    """Super simple shared memory implementation that uses a dictionary to store the entries.
    """

    def __init__(self):
        """Initialize the shared memory. In the current architecture the memory always consists of a set of soltuions or evaluations.
        Moreover, the project is designed around LLMs for the proof of concepts, so we treat all entry content as a string.
        """
        self.data = {}
        self.lock = threading.Lock()

    def add_entry(self, score, entry):
        """Add an entry to the internal memory.
        """
        raise NotImplementedError
    
    def get_top_n(self, n):
        """Get the top n entries from the internal memory.
        """
        raise NotImplementedError