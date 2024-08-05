import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.absolute()
os.environ['AS_PROJECT_ROOT'] = str(project_root)
print("Project root set to:", os.environ['AS_PROJECT_ROOT'])

from openai import OpenAI
from astra_assistants import patch
from agency_swarm.agency.agency import Agency
from agency_swarm.agents.agent import Agent
from agency_swarm.util.oai import set_openai_client
from dotenv import load_dotenv

load_dotenv(".env")

client = patch(OpenAI())

set_openai_client(client)

ceo = Agent(name="CEO",
            description="Responsible for client communication, task planning, and management.",
            instructions="Please communicate with users and other agents.",
            model="gemini/gemini-1.5-pro-latest",
            tools=[])

test_agent1 = Agent(name="agent1",
            description="Responsible for response.",
            instructions="Please communicate with other agents.",
            model="gemini/gemini-1.5-pro-latest",
            tools=[])
test_agent2 = Agent(name="agent2",
            description="Responsible for response.",
            instructions="Please communicate other agents.",
            model="gemini/gemini-1.5-pro-latest",
            tools=[])

agency = Agency([
    ceo,
    [ceo, test_agent1, test_agent2],
    [ceo, test_agent2],
])

# assistant = client.beta.assistants.retrieve(ceo.id)
# print(assistant)

# completion = agency.get_completion("What's something interesting about language models?",yield_messages=False)
# print(completion)
agency.demo_gradio()