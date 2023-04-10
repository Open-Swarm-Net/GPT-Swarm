import logging
from pathlib import Path

class CustomLogger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)

        self.log_folder = "logs"
        self.log_file = Path(f"{self.log_folder}/swarm.log")

        self.log_file.parent.mkdir(parents=True, exist_ok=True)