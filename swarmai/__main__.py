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
    try:
        os.environ["GOOGLE_API_KEY"] = keys["GOOGLE_API_KEY"]
        os.environ["CUSTOM_SEARCH_ENGINE_ID"] = keys["CUSTOM_SEARCH_ENGINE_ID"]
        os.environ["GOOGLE_CSE_ID"] = keys["CUSTOM_SEARCH_ENGINE_ID"]
    except:
        print("WARNING: GOOGLE_API_KEY and GOOGLE_CSE_ID not found in keys.json. Googler agent will be treated as a general purpose agent.")

    try:
        os.environ["APIFY_API_TOKEN"] = keys["APIFY_API_TOKEN"]
    except:
        print("WARNING: APIFY_API_TOKEN not found in keys.json. WebScraper agent will not work.")

def run_swarm(swarm_config_loc, agents_config_loc):
    # establishing the swarm
    swarm1 = Swarm(swarm_config_loc, agents_config_loc)
    swarm1.run_swarm()

if __name__=="__main__":
    swarm_config_loc = Path(__file__).parent.parent / "swarm_config.yaml"
    agents_config_loc = Path(__file__).parent.parent / "agents_config.yaml"
    load_keys()
    run_swarm(swarm_config_loc, agents_config_loc)