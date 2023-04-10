from swarmai.utils.memory.InternalMemoryBase import InternalMemoryBase
import uuid

class DictInternalMemory(InternalMemoryBase):

    def __init__(self, n_entries):
        """Initialize the internal memory. In the current architecture the memory always consists of a set of soltuions or evaluations.
        Simple key-value store for now.
        """
        super().__init__(n_entries)
        self.data = {}

    def add_entry(self, score, entry):
        """Add an entry to the internal memory.
        """
        random_key = str(uuid.uuid4())
        self.data[random_key] = {"score": score, "entry": entry}

        # keep only the best n entries
        sorted_data = sorted(self.data.items(), key=lambda x: x[1]["score"], reverse=True)
        self.data = dict(sorted_data[:self.n_entries])
    
    def get_top_n(self, n):
        """Get the top n entries from the internal memory.
        """
        sorted_data = sorted(self.data.items(), key=lambda x: x[1]["score"], reverse=True)
        return sorted_data[:n]