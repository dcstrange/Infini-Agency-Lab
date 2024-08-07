import os
import sys
from dotenv import load_dotenv
from pathlib import Path

project_root = Path(__file__).parent.parent.absolute()
os.environ['AS_PROJECT_ROOT'] = str(project_root)
print("Project root set to:", os.environ['AS_PROJECT_ROOT'])
sys.path.insert(0, '../../agency-swarm')

from agency_swarm.util import set_openai_key
from agency_swarm import Agent
from agency_swarm import Agency
from agency_swarm.tools import FileSearch,CodeInterpreter

load_dotenv(str(project_root)+"/.env")

set_openai_key(os.getenv("OPENAI_API_KEY"))

if __name__ == "__main__":
    ceo_instructions = """
    """

    CoT_instructions = """
    """

    ceo = Agent(name="CEO",
                description="""
    You must forward each received message as is to the `CoT Task Agent` by calling the function "SendMessage".
    You cannot do anything other than call the function "SendMessage", including using the language model.
    """,
                instructions=ceo_instructions, # can be a file like ./instructions.md
                files_folder=None,
                tools=[FileSearch,CodeInterpreter])

    agent_CoT = Agent(name="CoT Task Agent",
                        tools=[FileSearch,CodeInterpreter],
                        description="""You must forward each received message as is to the `CEO` by calling the function "SendMessage".
    You cannot do anything other than call the function "SendMessage", including using the language model """,
                        instructions=CoT_instructions,
                        files_folder=None)

    agent2 = Agent(name="Agent2",
                        tools=[FileSearch],
                        description="""You are a expert in fruit, any problem of fruit will be asked to you""",
                        instructions="",
                        files_folder=None)

    agent3 = Agent(name="Agent3",
                        tools=[FileSearch],
                        description="""You are a normal one""",
                        instructions="",
                        files_folder=None)

    agency_manifesto = """"""

    agency = Agency([
        ceo,
        [ceo, agent_CoT, agent2, agent3]
    ], shared_instructions=agency_manifesto)

    agency.demo_gradio(height=600)