from agency_swarm.agents import Agent


class APICaller(Agent):
    def __init__(self):
        super().__init__(
            name="API Caller",
            description="API Caller 发送请求来调用已经构造好的API。",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[],
            tools_folder="./tools",
            temperature=0.3,
            max_prompt_tokens=25000,
        )
        
    def response_validator(self, message):
        return message
