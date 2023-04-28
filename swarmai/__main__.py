import sys
import os
import json
from pathlib import Path
sys.path.append('..')

from swarmai.Swarm import Swarm

def load_keys():
    keys_file = Path(__file__).parent.parent / "keys.json"
    with open(keys_file) as f:
        keys = json.load(f)
    os.environ["OPENAI_API_KEY"] = keys["OPENAI_API_KEY"]

def run_swarm(challenge):
    # establishing the swarm
    swarm1 = Swarm((10,), {"manager": 3, "analyst": 9})
    swarm1.run_swarm(challenge, max_sec=120)

if __name__=="__main__":
    main_task =(
        "Act as an investement analyst. The startup described below is looking for funding. Your task is to find out as much as possible about the ideas space and startup's potential.\n"
        "Guardrails is an open-source Python package for specifying structure and type, validating and correcting the outputs of large language models (LLMs)."
    )
    load_keys()
    run_swarm(main_task)