from typing import List
import random

from gptswarm.utils.challenges.PythonChallenge import PythonChallengeSolutionBase

class Solution(PythonChallengeSolutionBase):
    def isIdealPermutation(self, A: List[int]) -> bool:
        for i in range(len(A)):
            if i - A[i] > 1 or i - A[i] < -1: return False
        return True
    
    def gen_random_input(self):
        """Generates and integer integer array nums of length n which represents a permutation of all the integers in the range [0, n - 1].
        is an ideal permuation if the number of global inversions is equal to the number of local inversions.
        """
        prob_of_ideal = 0.5
        if random.random() < prob_of_ideal:
            n = random.randint(1, 10)
            nums = list(range(n))
            random.shuffle(nums)
        else:
            n = random.randint(1, 10)
            nums = list(range(n))
            random.shuffle(nums)
            i = random.randint(0, n-1)
            j = random.randint(0, n-1)
            nums[i], nums[j] = nums[j], nums[i]
        return {"A": nums}
        
    def test_solution(self, test_func):
        test_input = self.gen_random_input()
        correct_result = self.isIdealPermutation(**test_input)

        try:
            result = test_func(**test_input)
        except Exception as e:
            return 0, f"{e}"
        
        if result == correct_result:
            return 1, f"Input: {test_input}\nResult: {result}\nExpected: {correct_result}\nCorrect: {True}\n"
        else:
            return 0, f"Input: {test_input}\nResult: {result}\nExpected: {correct_result}\nCorrect: {False}\n"
        


