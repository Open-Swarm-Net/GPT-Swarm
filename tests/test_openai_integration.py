import sys
import os
import json
sys.path.append('..')

from pathlib import Path
from gptswarm.utils.GPTCaller import GPTCaller

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
        
def test_openai_integration(model_name):
    keys_file = Path("../keys.json")
    with open(keys_file) as f:
        keys = json.load(f)
    os.environ["OPENAI_API_KEY"] = keys["OPENAI_API_KEY"]

    caller = GPTCaller({"model_name": model_name})
    conversation = [
        {"role": "system", "content": "act as a professional writer and expert in poems as well as AI and swarm intelligence."},
        {"role": "user", "content": "Write a cheerful poem under 100 words about how swarm intelligence is superior to single-model AI."}
    ]
    call_parameters = {
        "max_tokens": 500,
        "temperature": 0.5,
        "n": 1,
        "stop": None
    }

    # call the model
    response = caller.call_model(conversation, call_parameters)
    
    print(f"{bcolors.OKBLUE}TASK{bcolors.ENDC} => {conversation[1]['content']}")
    print(f"{bcolors.OKBLUE}RESPONSE{bcolors.ENDC} => \n {response}")

if __name__ == "__main__":
    test_openai_integration("gpt-3.5-turbo")
    test_openai_integration("text-davinci-003")