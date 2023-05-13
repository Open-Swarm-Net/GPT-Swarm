from .ManagerAgent import ManagerAgent
from .GeneralPurposeAgent import GeneralPurposeAgent
from .GooglerAgent import GooglerAgent
from .CrunchbaseSearcher import CrunchbaseSearcher

AGENT_ROLES = {
    "manager": ManagerAgent,
    "googler": GooglerAgent,
    "analyst": GeneralPurposeAgent,
    "crunchbase_searcher": CrunchbaseSearcher
}
