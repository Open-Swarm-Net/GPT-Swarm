import sys
import os
import json
from pathlib import Path
sys.path.append('..')

from swarmai.challenges.python_challenges.PythonChallenge import PythonChallenge
from swarmai.Swarm import Swarm

def load_keys():
    keys_file = Path(__file__).parent.parent / "keys.json"
    with open(keys_file) as f:
        keys = json.load(f)
    os.environ["OPENAI_API_KEY"] = keys["OPENAI_API_KEY"]

def init_challenge():
    # defining the challenge the swarm will be working on
    test_challenge_config = Path(__file__).parent.parent / 'swarmai/challenges/python_challenges/challenge2/pc2_config.yaml'
    challenge1 = PythonChallenge(test_challenge_config)
    print(challenge1.get_problem())
    return challenge1

def run_swarm(challenge):
    # establishing the swarm
    swarm1 = Swarm(challenge, (5, 5), {"python developer": 0.8, "explorer python": 0.2})
    swarm1.run_swarm(15000)

if __name__=="__main__":
    load_keys()
    ch = init_challenge()
    run_swarm(ch)