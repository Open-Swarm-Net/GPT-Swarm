import os
import sys
import yaml
import json
from pathlib import Path

sys.path.append(str(Path('__file__').parent.parent))
from swarmai.__main__ import run_swarm

"""
Define some global parameters.
This is a simple frontent for the swarm.

The swarm has a config, the default output and entry-point.

Default swarm config (for copilot =)):
swarm:
  agents: # supported: manager, analyst, googler, crunchbase_searcher
    - type: manager
      n: 2
    - type: analyst
      n: 2
    - type: googler
      n: 2
    - type: crunchbase_searcher # scraper can only have one job in parallel
      n: 1
  timeout_min: 10
  run_dir: ./tmp/swarm
task:
  role: |
    professional venture capital agency, who has a proven track reckord of consistently funding successful startups
  global_goal: |
    A new startup just send us their pitch. Find if the startup is worth investing in. The startup is called Brainamics and it is in the space of brain computer interfaces.
    More information about them: 'https://brainamics.de', 'https://www.linkedin.com/company/thebrainamics/'
  goals:
    - Generate a comprehensive description of the startup. Describe their value proposition, the product, USP and business model of a startup.
    - Find any mentions of the startup in the news, social media, etc. Add links.
    - Find top 10 companies and startups in this field. Find out their locations, raised funding, value proposition, differentiation, etc.
    - Find top 5 investors in this field. Includ specific details in the format of 'company AAA (link) invested in company BBB (link) $XX in year YYYY'
    - Describe the market size, growth rate and trends of this field.
    - Main problems and challenges of the field. Create an extensive list of problems. What can stop the field from growing? What can stop the company from succeeding?
    - Briefly describe the technology for the non-tech audience. Include links to the main articles in the field.
    - What questions should we ask the startup to make a more informed decision? Avoid generic and obvious questions and focus on field/domain specific questions that can uncover problems with this specific startup.

"""
SWARM_CONFIG_PATH = "swarm_config.yaml"
ALLOWED_AGENTS = ["manager", "analyst", "googler", "crunchbase_searcher"]

SWARM_DEFAULT_RUN_FOLDER = (Path("__file__").parent / "tmp" / "swarm").resolve()
SWARM_DEFAULT_JSON_OUTPUT = str(SWARM_DEFAULT_RUN_FOLDER / "output.json")
SWARM_DEAFAULT_LOGS = str(SWARM_DEFAULT_RUN_FOLDER / "swarm.json")
SWARM_DEFAULT_SHARED_MEMORY = str(SWARM_DEFAULT_RUN_FOLDER / "shared_memory")

def get_swarm_config():
    """
    Load the swarm config from the default location.
    """
    with open(SWARM_CONFIG_PATH) as f:
        swarm_config = yaml.load(f, Loader=yaml.FullLoader)
    return swarm_config

def set_swarm_role(role_description):
    """
    Set the role for the swarm. It's specified in the swarm_config.yaml file under: swarm.task.role
    """
    if role_description=="":
        role_description = "professional venture capital agency, who has a proven track reckord of consistently funding successful startups"
    swarm_config = get_swarm_config()
    print(f"Setting role to: {role_description}")
    swarm_config["task"]["role"] = role_description
    with open(SWARM_CONFIG_PATH, "w") as f:
        yaml.dump(swarm_config, f)
def get_swarm_role():
    """
    Get the role for the swarm. It's specified in the swarm_config.yaml file under: swarm.task.role
    """
    swarm_config = get_swarm_config()
    return swarm_config["task"]["role"]

def set_swarm_global_goal(global_goal):
    """
    Set the global goal for the swarm. It's specified in the swarm_config.yaml file under: swarm.task.global_goal
    """
    if global_goal=="":
        global_goal = "A new startup just send us their pitch. Find if the startup is worth investing in. The startup is called Brainamics and it is in the space of brain computer interfaces."
    swarm_config = get_swarm_config()
    print(f"Setting global goal to: {global_goal}")
    swarm_config["task"]["global_goal"] = global_goal
    with open(SWARM_CONFIG_PATH, "w") as f:
        yaml.dump(swarm_config, f)

def get_swarm_global_goal():
    """
    Get the global goal for the swarm. It's specified in the swarm_config.yaml file under: swarm.task.global_goal
    """
    swarm_config = get_swarm_config()
    return swarm_config["task"]["global_goal"]

def set_swarm_goals(goals: list):
    """
    Set the goals for the swarm. It's specified in the swarm_config.yaml file under: swarm.task.goals

    Default goals:
    - Generate a comprehensive description of the startup. Describe their value proposition, the product, USP and business model of a startup.
    - Find any mentions of the startup in the news, social media, etc. Add links.
    - Find top 10 companies and startups in this field. Find out their locations, raised funding, value proposition, differentiation, etc.
    - Find top 5 investors in this field. Includ specific details in the format of 'company AAA (link) invested in company BBB (link) $XX in year YYYY'
    - Describe the market size, growth rate and trends of this field.
    - Main problems and challenges of the field. Create an extensive list of problems. What can stop the field from growing? What can stop the company from succeeding?
    - Briefly describe the technology for the non-tech audience. Include links to the main articles in the field.
    - What questions should we ask the startup to make a more informed decision? Avoid generic and obvious questions and focus on field/domain specific questions that can uncover problems with this specific startup.
    """
    try:
        if len(goals) == 0:
            raise ValueError("Goals can't be empty.")
        
        all_empty = True
        for idx, goal in enumerate(goals):
            if goal != "":
                all_empty = False
                break
            else:
                # remove empty goals
                goals.pop(idx)
        if not all_empty:
            raise ValueError("Goals can't be empty.")
    except ValueError:
        goals = [
            "Generate a comprehensive description of the startup. Describe their value proposition, the product, USP and business model of a startup.",
            "Find any mentions of the startup in the news, social media, etc. Add links.",
            "Find top 10 companies and startups in this field. Find out their locations, raised funding, value proposition, differentiation, etc.",
            "Find top 5 investors in this field. Includ specific details in the format of 'company AAA (link) invested in company BBB (link) $XX in year YYYY'",
            "Describe the market size, growth rate and trends of this field.",
            "Main problems and challenges of the field. Create an extensive list of problems. What can stop the field from growing? What can stop the company from succeeding?",
            "Briefly describe the technology for the non-tech audience. Include links to the main articles in the field.",
            "What questions should we ask the startup to make a more informed decision? Avoid generic and obvious questions and focus on field/domain specific questions that can uncover problems with this specific startup."
        ]
    swarm_config = get_swarm_config()
    print(f"Setting goals to: {goals}")
    swarm_config["task"]["goals"] = goals
    with open(SWARM_CONFIG_PATH, "w") as f:
        yaml.dump(swarm_config, f)

def get_swarm_goals():
    """
    Get the goals for the swarm. It's specified in the swarm_config.yaml file under: swarm.task.goals
    """
    swarm_config = get_swarm_config()
    return swarm_config["task"]["goals"]

def set_swarm_agents_config(agents_config: list):
    """
    Set the agents config for the swarm. It's specified in the swarm_config.yaml file under: swarm.agents
    """
    try:
        if len(agents_config) == 0:
            raise ValueError("No agents config specified.")
        for agent_config in agents_config:
            if "type" not in agent_config:
                raise ValueError(f"Agent config {agent_config} does not have a type specified.")
            if agent_config["type"] not in ALLOWED_AGENTS:
                raise ValueError(f"Agent type {agent_config['type']} is not supported. Supported agents: {ALLOWED_AGENTS}")
            if "n" not in agent_config:
                raise ValueError(f"Agent config {agent_config} does not have a number of agents specified.")
            if agent_config["n"] == '':
                raise ValueError(f"Agent config {agent_config} does not have a number of agents specified.")
            if agent_config["n"] < 0:
                raise ValueError(f"Agent config {agent_config} has a negative number of agents specified.")
            if agent_config["n"] > 100:
                raise ValueError(f"Agent config {agent_config} has a number of agents specified that is too large. Max number of agents is 10.")
    except ValueError as e:
        agents_config = [
            {"type": "manager", "n": 2},
            {"type": "analyst", "n": 2},
            {"type": "googler", "n": 2},
        ]
    swarm_config = get_swarm_config()
    print(f"Setting agents config to: {agents_config}")
    swarm_config["swarm"]["agents"] = agents_config
    with open(SWARM_CONFIG_PATH, "w") as f:
        yaml.dump(swarm_config, f)
def get_swarm_agents_config():
    """
    Get the agents config for the swarm. It's specified in the swarm_config.yaml file under: swarm.agents
    """
    swarm_config = get_swarm_config()
    return swarm_config["swarm"]["agents"]

def read_swarm_output():
    """
    Read the output of the swarm. The file can sometimes be locked by the swarm, so we need to handle this.
    """
    try:
        with open(SWARM_DEFAULT_JSON_OUTPUT) as f:
            final_out = ""
            output = json.load(f)
            for _, value in output.items():
                final_out+="========================================\n"
                final_out+="========================================\n"
                for key, value in value.items():
                    final_out+=f"**{key}**:\n{value}\n\n"
            f.close()
    except Exception:
        final_out = "Swarm is starting up (needs ~2-3 minutes for first results and ~30 sec for first logs)..."
    return final_out

def read_swarm_logs():
    """
    Read the logs of the swarm. The file can sometimes be locked by the swarm, so we need to handle this.
    """
    try:
        with open(SWARM_DEAFAULT_LOGS) as f:
            # read last 100 lines
            logs = f.readlines()[-100:]
            final_out = "\n".join(logs)
            f.close()
    except Exception:
        final_out = "Swarm is starting up..."
    return final_out

def execute_swarm():
    run_swarm()