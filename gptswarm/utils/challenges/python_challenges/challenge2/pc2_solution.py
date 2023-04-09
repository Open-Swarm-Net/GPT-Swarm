from typing import List
import random
import string
import time

from gptswarm.utils.challenges.PythonChallenge import PythonChallengeSolutionBase

class Solution(PythonChallengeSolutionBase):
    def strongPasswordChecker(self, s: str) -> int:
        """
        :type s: str
        :rtype: int
        """
        missing_type = 3
        if any('a' <= c <= 'z' for c in s): missing_type -= 1
        if any('A' <= c <= 'Z' for c in s): missing_type -= 1
        if any(c.isdigit() for c in s): missing_type -= 1

        change = 0
        one = two = 0
        p = 2
        while p < len(s):
            if s[p] == s[p-1] == s[p-2]:
                length = 2
                while p < len(s) and s[p] == s[p-1]:
                    length += 1
                    p += 1
                    
                change += length // 3
                if length % 3 == 0: one += 1
                elif length % 3 == 1: two += 1
            else:
                p += 1
        
        if len(s) < 6:
            return max(missing_type, 6 - len(s))
        elif len(s) <= 20:
            return max(missing_type, change)
        else:
            delete = len(s) - 20
            
            change -= min(delete, one)
            change -= min(max(delete - one, 0), two * 2) // 2
            change -= max(delete - one - 2 * two, 0) // 3
                
            return delete + max(missing_type, change)
    
    def random_password(self, size):
        chars = string.ascii_letters + string.digits + '.!'
        return ''.join(random.choice(chars) for _ in range(size))

    def gen_random_input(self):
        """Bad cases:
        - has 3 repeating characters in a row
        - doesn't have a number
        - doesn't have a lowercase letter
        - doesn't have an uppercase letter
        """
        # Generate random password length between 1 and 50
        password_length = random.randint(1, 50)
        password = self.random_password(password_length)

        # Check if password has 3 repeating characters in a row
        for i in range(len(password) - 2):
            if password[i] == password[i+1] == password[i+2]:
                break

        # with 50% chance, mess up the password
        if random.random() < 0.5:
            rand = random.random()
            if rand < 0.25:
                password = ''.join([c for c in password if not c.isdigit()])
            elif rand < 0.5:
                password = ''.join([c for c in password if not c.islower()])
            elif rand < 0.75:
                password = ''.join([c for c in password if not c.isupper()])
            else:
                random_char = random.choice(string.ascii_letters + string.digits)
                len_rep = random.randint(3, 10)
                rep_str = random_char*len_rep
                # insert the triplet rep_str at a random position
                pos = random.randint(0, len(password))
                password = password[:pos] + rep_str + password[pos:]

        if len(password) == 0:
            # in case we removed all characters, generate a new password
            password_length = random.randint(2, 40)
            password = self.random_password(password_length)

        return password

    def evaluate_solution(self, test_func, n_tests=10000):
        """Evaluates whatever you want. The evaluation function is absolutely flexible.
        """
        default_cases = [
            "a",
            "aA1",
            "1337C0d3",
            "aaa123",
            "aaa111",
            "ssSsss",
            "ABABABABABABABABABAB1",
            "bbaaaaaaaaaaaaaaacccccc",
            "aaaaAAAAAA000000123456",
            "aaaabbbbccccddeeddeeddeedd",
            "FFFFFFFFFFFFFFF11111111111111111111AAA",
            "A1234567890aaabbbbccccc",

        ]

        test_cases = default_cases*int(n_tests/(len(default_cases)*2)) + [self.gen_random_input() for _ in range(int(n_tests/2))]
        correct_solutions = []
        test_solutions = []

        # create ideal solutions and also time it
        tick = time.time()
        for test_case in test_cases:
            correct_solutions.append(self.strongPasswordChecker(s=test_case))
        tock = time.time()
        ideal_time = (tock - tick)

        # create test solutions and also time it
        tick = time.time()
        for test_case in test_cases:
            if time.time()-tick > 10:
                test_solutions.append(0)
            else:
                test_solutions.append(test_func(s=test_case))
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
        


