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

def run_swarm(swarm_config_loc):
    # establishing the swarm
    swarm1 = Swarm(swarm_config_loc)
    swarm1.run_swarm()

if __name__=="__main__":
    swarm_config_loc = Path(__file__).parent.parent / "swarm_config.yaml"
    load_keys()
    run_swarm(swarm_config_loc)