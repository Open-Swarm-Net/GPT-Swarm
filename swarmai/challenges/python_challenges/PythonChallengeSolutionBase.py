from abc import ABC, abstractmethod
import threading
import types
from typing import Tuple

class PythonChallengeSolutionBase(ABC):
    """Base class for the solution that every solution must implement
    """
    def __init__(self):
        pass

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