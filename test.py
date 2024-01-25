import os
from agency_swarm import set_openai_key
from getpass import getpass


from agency_swarm import Agent
from agency_swarm import Agency

set_openai_key(getpass("Please enter your openai key: "))



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
            tools=[])

agent_CoT = Agent(name="CoT Task Agent",
                     tools=[],
                     description="""You must forward each received message as is to the `CEO` by calling the function "SendMessage".
You cannot do anything other than call the function "SendMessage", including using the language model """,
                     instructions=CoT_instructions,
                     files_folder=None)

agency_manifesto = """"""

agency = Agency([
    ceo,
    [ceo, agent_CoT],
    [agent_CoT, ceo]
], shared_instructions=agency_manifesto)

agency.demo_gradio(height=900)