import sys
import os
import json
import time
from pathlib import Path
sys.path.append('..')

from swarmai.Swarm import Swarm

from swarmai.utils.notion.JsonOrder import reorder_json
from swarmai.utils.notion.NotionPublish import publish_to_notion


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

    try:
        os.environ["NOTION_API_KEY"] = keys["NOTION_API_KEY"]
        os.environ["NOTION_DATABASE_ID"] = keys["NOTION_DATABASE_ID"]
        os.environ["OUTPUT_PATH_JSON"] = keys["OUTPUT_PATH_JSON"]
    except:
        print("WARNING: Notion related keys not found in keys.json. Notion publish will not work.")
def run_swarm(swarm_config_loc):
    # establishing the swarm
    swarm1 = Swarm(swarm_config_loc)
    swarm1.run_swarm()

if __name__=="__main__":
    swarm_config_loc = Path(__file__).parent.parent / "swarm_config.yaml"
    load_keys()
    run_swarm(swarm_config_loc)
    
    # Wait for 630 seconds when ./run.sh finished
    time.sleep(630)

    # Reorder JSON
    input_file = Path(__file__).parent.parent / 'tmp/swarm/output.json'
    output_file = Path(__file__).parent.parent / 'tmp/swarm/output_ordered.json'
    print(input_file)
    print(output_file)
    reorder_json(input_file, output_file)


    # Publish to Notion
    notion_api_key = os.environ["NOTION_API_KEY"]
    notion_database_id = os.environ["NOTION_DATABASE_ID"]
    publish_to_notion(notion_api_key, notion_database_id, output_file)
