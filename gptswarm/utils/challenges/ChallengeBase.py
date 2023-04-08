from abc import ABC, abstractmethod

class ChallengeBase(ABC):
    """The base class that allows the swarm to get the problem and test and evaluate it's solutions.
    """

    @abstractmethod
    def get_problem(self):
        """Returns the problem to be solved.
        """
        pass

    @abstractmethod
    # accepts a string and returns a float score and a string output or error
    def evaluate_solution(self, solution: str):
        """Tests a solution to the problem.

        Args:
            solution (str): The solution as string

        Returns:
            float: The score of the solution
            str: The output of the solution including possible errors
        """
        pass

