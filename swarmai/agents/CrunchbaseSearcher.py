from swarmai.agents.AgentBase import AgentBase
from swarmai.utils.ai_engines import LanchainGoogleEngine, GPTConversEngine
from swarmai.utils.task_queue.Task import Task
from swarmai.utils.PromptFactory import PromptFactory
from langchain.utilities import ApifyWrapper

class CrunchbaseSearcher(AgentBase):
    """Very custom agent that can search for companies on Crunchbase and analyse them.
    """

    def __init__(self, agent_id, agent_type, swarm, logger):
        super().__init__(agent_id, agent_type, swarm, logger)
        self.search_engine = LanchainGoogleEngine("gpt-3.5-turbo", 0.5, 1000)
        self.thinking_engine = GPTConversEngine("gpt-3.5-turbo", 0.5, 1000)
        
        self.TASK_METHODS = {
            Task.TaskTypes.crunchbase_search: self.domain_specific_search,
        }

        self.apify_engine = ApifyWrapper()

    def perform_task(self):
        self.step = "perform_task"
        try:
            # self.task is already taken in the beginning of the cycle in AgentBase
            if not isinstance(self.task, Task):
                raise Exception(f"Task is not of type Task, but {type(self.task)}")
            
            task_type = self.task.task_type
            if task_type not in self.TASK_METHODS:
                raise Exception(f"Task type {task_type} is not supported by the agent {self.agent_id} of type {self.agent_type}")
            
            self.result = self.TASK_METHODS[task_type](self.task.task_description)
            return True
        except Exception as e:
            self.log(message = f"Agent {self.agent_id} of type {self.agent_type} failed to perform the task {self.task.task_description} with error {e}", level = "error")
            return False
        
    def share(self):
        pass

    def domain_specific_search(self, task_description):
        self.step = "crunchbase_search"

        prompt = (
            f"based on the task description:\n{task_description}\n\ngenerate a short google search query under 5 words to find relevant companies on Crunchbase"
        )
        conversation = [
            {"role": "user", "content": prompt},
        ]

        search_query = self.thinking_engine.call_model(conversation)
        # remove ", \n, \t, ', from the search query
        search_query = search_query.lower().replace('"', "").replace("\n", "").replace("\t", "").replace("'", "").replace("’", "").replace("crunchbase", "")
        search_query += " site:crunchbase.com/organization"
        
        # getting the relevant links:
        sources = self.search_engine.search_sources(search_query, n=5)
        if len(sources) == 0:
            self.log(message = f"Agent {self.agent_id} of type {self.agent_type} failed to find any relevant links for the task {task_description}", level = "error")
            return None
        
        if 'Result' in sources[0]:
            if sources[0]['Result'] == 'No good Google Search Result was found':
                self.log(message = f"Agent {self.agent_id} of type {self.agent_type} failed to find any relevant links for the task {task_description}", level = "error")
                return None

        links = [item["link"] for item in sources]
        
        company_infos = ""
        for link in links:
            company_infos += self._get_crunchbase_data(link)

        self._send_data_to_swarm(company_infos)
        self.log(message = f"Agent {self.agent_id} of type {self.agent_type} search:\n{task_description}\n\nand got:\n{company_infos}", level = "info")

        return company_infos

    def _get_crunchbase_data(self, url):
        loader = self.apify_engine.call_actor(
            actor_id="epctex/crunchbase-scraper",
            run_input={"startUrls": [url],"proxy": {
            "useApifyProxy": True
        },},
            dataset_mapping_function=self._crunchbase_dataset_mapping_function
        )
        return loader.load().__repr__()
    
    def _crunchbase_dataset_mapping_function(self, parsed_data):
        mapped_data = {}

        # Mapping properties
        properties = parsed_data.get("properties", {})
        identifier = properties.get("identifier", {})
        cards = parsed_data.get("cards", {})
        company = cards.get("company_about_fields2", {})
        funding_summary = parsed_data.get("cards", {}).get("funding_rounds_summary", {})
        funding_total = funding_summary.get("funding_total", {})

        mapped_data["title"] = properties.get("title")
        mapped_data["short_description"] = properties.get("short_description")
        mapped_data["website"] = company.get("website", {}).get("value")
        
        mapped_data["country"] = None
        for location in company.get("location_identifiers", []):
            if location.get("location_type") == "country":
                mapped_data["country"] = location.get("value")
                break
        mapped_data["value_usd"] = funding_total.get("value_usd")


        # Mapping cards
        cards = parsed_data.get("cards", {})
        return mapped_data