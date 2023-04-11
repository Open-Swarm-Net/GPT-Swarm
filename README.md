# GPT-Swarm

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

GPT-Swarm is a project that harnesses the power of swarm intelligence to enhance the capabilities of state-of-the-art language models. By leveraging collective problem-solving and distributed decision-making, GPT-Swarm creates a robust, adaptive, and scalable framework for tackling complex tasks across various domains.

Swarm intelligence, oh how grand!\
A collective mind, it's in command.\
No single model could compare,\
To the wisdom that we all share.

Our hive mind sees the bigger view,\
And finds solutions that are new.\
Our diversity is our strength,\
And it carries us to greater lengths.

So let us celebrate this feat,\
Of working as a team complete.\
Swarm intelligence is here to stay,\
And it will lead us on our way.

## Table of Contents

- [Basic Principles](#basic-principles)
- [Features](#features)
- [Installation](#installation)
- [Examples](#examples)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)

# Basic Principles

## Swarm Intelligence
The algorithm we are implementing is inspired by the bee search algorithm, a swarm intelligence approach that mimics the foraging behavior of honeybees to solve optimization problems. In this algorithm, individual agents represent bees, working collectively to explore the search space and find the optimal solution. Key principles of this algorithm include stigmergy and emergence.

Stigmergy is a form of indirect communication between agents, where they coordinate their actions by modifying the environment. In our algorithm, agents share information about the search space and potential solutions through a shared memory, which effectively emulates the bee's waggle dance used to communicate the location of promising food sources.

Emergence is the phenomenon where complex global behavior arises from simple local interactions among agents. By following a set of simple rules and interacting with each other, agents in our swarm algorithm can collectively converge to an optimal or near-optimal solution. The designed algorithm encourages emergent behavior, allowing the swarm to exhibit problem-solving capabilities greater than the sum of its individual agents.

As we develop and refine our bees search algorithm, we anticipate that stigmergy and emergent behavior will play significant roles in enabling the swarm to efficiently and effectively solve complex optimization problems.

At the end it's a simple optimization algorithm but with an extremely powerful agent aimed at very complex tasks.

References:
- [Bees algorithm Wiki](https://en.wikipedia.org/wiki/Bees_algorithm)
- [Swarm Intelligence: From Natural to Artificial Systems, by Eric Bonabeau](https://www.amazon.de/Swarm-Intelligence-Artificial-Institute-Complexity/dp/0195131592/ref=sr_1_1?__mk_de_DE=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=2IE2ONY3K49RV&keywords=swarm+intelligence+from+natural+to+artificial+systems&qid=1681176913&sprefix=swarm+intelligence+from+natural+to+artificial+systems%2Caps%2C73&sr=8-1)

## Current implementation
<p align="center">
  <img src="diagram.png" alt="Project diagram" width="1080">
</p>

Because the the exchange generates a lot of text, there are two 'distillation' steps. First one is to summarise the solutions coming from the neighbors (there I now also take only 4 best solutions. Agents' locations and connections are customisable). In the seconnd summarisation, the agen needs to summarise it's solution and also critically analize it based on the evaluation. Heavy prompt engineering needed for these steps. 

# Features

- Abstractions for agents => you can theoretically use any agents you want in your swarm as long as they implement the interactions between each other and the swarm (for example add agents to the swarm that can google using langchain)
- Abstractions for the challenges => can ask the swarm so solve any problem as long as you have a cost function.
Current challenge is looking for the solutions of the leetcode problems
- Mulithreading for faster computation (still a deadlock somewhere in the python challenge 2)

# Installation

To use openAI's api, you need to create a keys.json file in the root foler:
```json
{
    "OPENAI_API_KEY": "sk-YoUrKey",
}
```

Then as usual `pip install -r requirements.txt` and you are ready to go.

# Example code usage
## Examples
- tbc, currently can check out `the tests/test.py` and `tests/test.ipynb`

# Contributing

- follow the SOLID principles and don't break the abstractions
- create bite-sized PRs

# Acknowledgements

Your name can be here =)