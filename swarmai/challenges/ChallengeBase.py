from abc import ABC, abstractmethod
import threading

def synchronized(method):
    def wrapper(self, *args, **kwargs):
        with self.lock:
            self.lock.acquire(timeout = 5)
            try:
                return method(self, *args, **kwargs)
            except Exception as e:
                print(f"Failed to execute {method.__name__}: {e}")
            finally:
                self.lock.release()
    return wrapper

class ChallengeBase(ABC):
    """The base class that allows the swarm to get the problem and test and evaluate it's solutions.
    """
    def __init__(self):
        self.lock = threading.Lock()

    @synchronized
    @abstractmethod
    def get_problem(self):
        """Returns the problem to be solved.
        """
        pass
    
    @synchronized
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