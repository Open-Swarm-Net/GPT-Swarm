from typing import List
import random
import time

from swarmai.challenges.python_challenges.PythonChallengeSolutionBase import PythonChallengeSolutionBase

class Solution(PythonChallengeSolutionBase):
    def _isIdealPermutation(self, A: List[int]) -> bool:
        return all(abs(ind - num) <= 1 for ind, num in enumerate(A))
    
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
        
    def evaluate_solution(self, test_func, n_tests=10000):
        """Evaluates whatever you want. The evaluation function is absolutely flexible.
        """
        default_cases = [
            [1, 0, 2],
            [1, 2, 0],
            [0, 2, 1, 3]
        ]

        test_cases = default_cases*int(n_tests/2) + [self.gen_random_input() for _ in range(int(n_tests/2))]
        correct_solutions = []
        test_solutions = []

        # create ideal solutions and also time it
        tick = time.time()
        for test_case in test_cases:
            correct_solutions.append(self._isIdealPermutation(A=test_case.copy()))
        tock = time.time()
        ideal_time = (tock - tick)

        # create test solutions and also time it
        tick = time.time()
        for test_case in test_cases:
            test_solutions.append(test_func(A=test_case.copy()))
        tock = time.time()
        test_time = (tock - tick)

        # compare solutions
        correct = 0
        correct_list = []
        for i in range(len(test_cases)):
            if correct_solutions[i] == test_solutions[i]:
                correct += 1
                correct_list.append(True)
            else:
                correct_list.append(False)
        
        correctness_score = correct / len(test_cases)
        if ideal_time == 0 and test_time == 0:
            runtime_score = 1
        elif ideal_time == 0:
            ideal_time = test_time / 2
            runtime_score =  ideal_time / test_time
        elif test_time == 0:
            runtime_score = 1
        else:
            runtime_score =  ideal_time / test_time
        score = pow(correctness_score, 2)*pow(runtime_score, 1)
        print(f"Weighted score: {score:.2f}, correctness_score: {correctness_score}, runtime_score: {runtime_score}")

        if score == 1:
            evaluations = f"Everything is correct. \n Runtime: {test_time*1000:.3f}ms"
        else:
            evaluations = f"Total score: {score:.3f}; {correctness_score*100:.2f}% test cases are solved correctly; \n Runtime: {test_time*1000:.3f}ms, which is {1/runtime_score:.3f} times slower than the ideal solution."
            if correctness_score == 1:
                evaluations += "\n All test cases are solved correctly, but the runtime is too slow."
            else:
                evaluations += "\n Some test cases are solved incorrectly. Examples: \n"
                false_ids = [i for i, x in enumerate(correct_list) if x == False]
                n_examples = 5
                false_ids = random.sample(false_ids, min(n_examples, len(false_ids)))
                for false_id in false_ids:
                    evaluations += f"Input: {test_cases[false_id]}\nResult: {test_solutions[false_id]}\nExpected: {correct_solutions[false_id]}\nCorrect: {False}\n"
                

        return score, evaluations


