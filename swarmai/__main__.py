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
        "act as a professional hypercasual game designer, who has a proven track reckord of releasing ultra-successfull hypercasual games that earn millions of dollars per year. Your job is to come up with new original. Let's start with defining the principles of hypercasual game design."
        "Come up with ideas in the idea space of 'destruction'. You can combine ideas from above. Be so creative, as if you took magic mushrooms. Combine and mix the mechanics in crazy ways, making them overly complex, but then simplify them."
    )
    load_keys()
    run_swarm(main_task)