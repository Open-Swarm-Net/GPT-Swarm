from abc import ABC, abstractmethod

class RewardFunctionBase:
    """The reward function class is an abstract class for the reward function that is used to evaluate the performance of the swarm.
    The reward function is used to evaluate the performance of the swarm, and is used to calculate the reward that each worker gets.
    """
    def __init__(self):
        pass

    @abstractmethod
    def calculate_reward(self, solution: str) -> float:
        pass