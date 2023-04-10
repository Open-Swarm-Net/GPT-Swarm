from abc import ABC, abstractmethod
from typing import Tuple
import yaml
import sys
import types
import importlib.util
import re
from pathlib import Path

from swarmai.challenges.ChallengeBase import ChallengeBase

class PythonChallengeSolutionBase(ABC):
    """Base class for the solution that every solution must implement
    """
    @abstractmethod    
    def evaluate_solution(self, test_func: types.FunctionType) -> Tuple[float, str]:
        """Evaluates whatever you want. The evaluation function is absolutely flexible.
        Args:
            test_func (types.FunctionType): The function that is created from the submitted code

        Returns:
            float: score of the solution. Is between 0 and 1. Can be non-binary if we want to evaluate by the closeness of the solution to the correct one.
            str: output of the solution including possible errors.
        """
        raise NotImplementedError("test_solution method must be implemented in the derived class")        

class PythonChallenge(ChallengeBase):
    def __init__(self, config_file):
        """You can find the problem config in the python challenges folder.
        I took some problems from leetcode. If someone can do an easy leetcode integration, would be cool. This class and ChallengeBase provide wrappers.

        Args:
            problem_config (_type_): _description_

        TODO: evaluate the runtime and memory usage of the submitted code
        """
        config_file_loc = Path(config_file)
        self.config = self._load_config(config_file)

        # unpack the problem config
        self.problem_id = self.config['problem_id']
        self.problem_name = self.config['problem_name']
        self.problem_statement_file = self.config['problem_statement_file'] # txt file
        self.function_name = self.config['function_name'] # name of the function that needs to be implemented by LLM and executed by us for testing
        self.solution_file = self.config['solution_file'] # python file with a Solution class that inherits from PythonChallengeSolutionBase

        # fixing the paths
        self.solution_file = config_file_loc.parent / self.solution_file
        self.problem_statement_file = config_file_loc.parent / self.problem_statement_file

        # importing the solution as a module
        self.solution_module = self._import_solution_module(self.solution_file)

    def _load_config(self, config_file):
        with open(config_file, 'r') as file:
            config_data = yaml.safe_load(file)
        return config_data
    
    def _load_submitted_code(self, code: str):
        code = self._extract_code_block(code)
        module = types.ModuleType(self.function_name)
        exec(code, module.__dict__)
        sys.modules[self.function_name] = module
        return module
        
    def _extract_code_block(self, text: str) -> str:
        pattern = r'```python(.*?)```'
        match = re.search(pattern, text, re.DOTALL)

        if match:
            return match.group(1)
        else:
            raise ValueError("No valid code block found in the submitted solution")
    
    def _import_solution_module(self, solution_file):
        spec = importlib.util.spec_from_file_location("solution_module", solution_file)
        solution_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(solution_module)
        solution_instance = solution_module.Solution()
        return solution_instance
    
    def get_problem(self):
        """Returns a coding problem to be solved as a string.
        """
        with open(self.problem_statement_file, 'r') as file:
            problem_statement = file.read()
        return problem_statement
    
    def evaluate_solution(self, submitted_solution: str, num_test_cases=2000):
        """Python code of the potential solution is given by the LLM as a string.
        Therefore we first need to execute it.
        Then we need to test the solution from the Solution class in the solution python file.

        Args:
            solution (str): The solution as string

        Returns:
            float: The score of the solution
            str: The output of the solution including possible errors

        TODO: implement traceback printing for errors
        """
        error_base = f"Error during loading submitted code. Make sure you enclose your code in ```python\n ```, include a function with the name {self.function_name}, and have all the necessary imports."
        try:
            module = self._load_submitted_code(submitted_solution)
            func = getattr(module, self.function_name)
        except ValueError as ve:
            return 0, f"{error_base}\nError: {str(ve)}"
        except Exception as e:
            return 0, f"{error_base}\nError: {e}"

        score, eval = self.solution_module.evaluate_solution(func, n_tests=num_test_cases)
        return score, eval
