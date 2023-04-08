from typing import List
import random

from gptswarm.utils.challenges.PythonChallenge import PythonChallengeSolutionBase

class Solution(PythonChallengeSolutionBase):
    def _isIdealPermutation(self, A: List[int]) -> bool:
        for i in range(len(A)):
            if i - A[i] > 1 or i - A[i] < -1: return False
        return True
    
    def gen_random_input(self):
        """Generates and integer integer array nums of length n which represents a permutation of all the integers in the range [0, n - 1].
        is an ideal permuation if the number of global inversions is equal to the number of local inversions.
        """
        equal_inversions = random.choice([True, False])
        n = random.randint(2, 100)
        nums = list(range(n))
        
        if equal_inversions:
            for i in range(n - 1):
                if nums[i] > nums[i + 1]:
                    nums[i], nums[i + 1] = nums[i + 1], nums[i]
        else:
            i = random.randint(0, n - 2)
            j = random.randint(i + 1, n - 1)
            nums[i], nums[j] = nums[j], nums[i]

        return nums
        
    def test_solution(self, test_func):
        test_input = self.gen_random_input()
        correct_result = self._isIdealPermutation(A=test_input.copy())

        try:
            result = test_func(A=test_input.copy())
        except Exception as e:
            return 0, f"{e}"
        
        if result == correct_result:
            return 1, f"Input: {test_input}\nResult: {result}\nExpected: {correct_result}\nCorrect: {True}\n"
        else:
            return 0, f"Input: {test_input}\nResult: {result}\nExpected: {correct_result}\nCorrect: {False}\n"
        


