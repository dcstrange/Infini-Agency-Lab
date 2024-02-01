# Agency Swarm

[![Framework](https://firebasestorage.googleapis.com/v0/b/vrsen-ai/o/public%2Fyoutube%2FFramework.png?alt=media&token=ae76687f-0347-4e0c-8342-4c5d31e3f050)](https://youtu.be/M5Pa0pLgyYU?si=f-cQV8FoiGd98uuk)

## Overview

Agency Swarm is an open-source agent orchestration framework designed to automate and streamline AI development processes. Leveraging the power of the OpenAI Assistants API, it enables the creation of a collaborative swarm of agents (Agencies), each with distinct roles and capabilities. This framework aims to replace traditional AI development methodologies with a more dynamic, flexible, and efficient agent-based system.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1qGVyK-vIoxZD0dMrMVqCxCsgL1euMLKj)
[![Subscribe on YouTube](https://img.shields.io/youtube/channel/subscribers/UCSv4qL8vmoSH7GaPjuqRiCQ
)](https://youtube.com/@vrsen/)
[![Follow on Twitter](https://img.shields.io/twitter/follow/__vrsen__.svg?style=social&label=Follow%20%40__vrsen__)](https://twitter.com/__vrsen__)

## Key Features

- **Customizable Agent Roles**: Define roles like CEO, virtual assistant, developer, etc., and customize their functionalities with [Assistants API](https://platform.openai.com/docs/assistants/overview).
- **Full Control Over Prompts**: Avoid conflicts and restrictions of pre-defined prompts, allowing full customization.
- **Tool Creation**: Tools within Agency Swarm are created using [Instructor](https://github.com/jxnl/instructor), which provides a convenient interface and automatic type validation. 
- **Efficient Communication**: Agents communicate through a specially designed "send message" tool based on their own descriptions.
- **State Management**: Agency Swarm efficiently manages the state of your assistants on OpenAI, maintaining it in a special `settings.json` file.

## Installation

```bash
pip install git+https://github.com/VRSEN/agency-swarm.git
```

## Getting Started


1. **Set Your OpenAI Key**:

```python
from agency_swarm import set_openai_key
set_openai_key("YOUR_API_KEY")
```

2. **Create Tools**:
Define your custom tools with [Instructor](https://github.com/jxnl/instructor):
```python
from agency_swarm.tools import BaseTool
from pydantic import Field

class MyCustomTool(BaseTool):
    """
    A brief description of what the custom tool does. 
    The docstring should clearly explain the tool's purpose and functionality.
    """

    # Define the fields with descriptions using Pydantic Field
    example_field: str = Field(
        ..., description="Description of the example field, explaining its purpose and usage."
    )

    # Additional fields as required
    # ...

    def run(self):
        """
        The implementation of the run method, where the tool's main functionality is executed.
        This method should utilize the fields defined above to perform its task.
        Doc string description is not required for this method.
        """

        # Your custom tool logic goes here
        do_something(self.example_field)

        # Return the result of the tool's operation
        return "Result of MyCustomTool operation"
```
Import in 1 line of code from [Langchain](https://python.langchain.com/docs/integrations/tools):

```python
from langchain.tools import YouTubeSearchTool
from agency_swarm.tools import ToolFactory

LangchainTool = ToolFactory.from_langchain_tool(YouTubeSearchTool)
```

```python
from langchain.agents import load_tools

tools = load_tools(
    ["arxiv", "human"],
)

tools = ToolFactory.from_langchain_tools(tools)
```

**NEW**: Convert from OpenAPI schemas:

```python
# using local file
with open("schemas/your_schema.json") as f:
    ToolFactory.from_openapi_schema(
        f.read(),
    )

# using requests
ToolFactory.from_openapi_schema(
    requests.get("https://api.example.com/openapi.json").json(),
)
```


3. **Define Agent Roles**: Start by defining the roles of your agents. For example, a CEO agent for managing tasks and a developer agent for executing tasks.

```python
from agency_swarm import Agent

ceo = Agent(name="CEO",
            description="Responsible for client communication, task planning and management.",
            instructions="You must converse with other agents to ensure complete task execution.", # can be a file like ./instructions.md
            files_folder="./files", # files to be uploaded to OpenAI
            schemas_folder="./schemas", # OpenAPI schemas to be converted into tools
            tools=[MyCustomTool, LangchainTool])
```

Import from existing agents:

```python
from agency_swarm.agents.browsing import BrowsingAgent

browsing_agent = BrowsingAgent()

browsing_agent.instructions += "\n\nYou can add additional instructions here."
```



4. **Define Agency Communication Flows**: 
Establish how your agents will communicate with each other.

```python
from agency_swarm import Agency

agency = Agency([
    ceo,  # CEO will be the entry point for communication with the user
    [ceo, dev],  # CEO can initiate communication with Developer
    [ceo, va],   # CEO can initiate communication with Virtual Assistant
    [dev, va]    # Developer can initiate communication with Virtual Assistant
], shared_instructions='agency_manifesto.md') # shared instructions for all agents
```

 In Agency Swarm, communication flows are directional, meaning they are established from left to right in the agency_chart definition. For instance, in the example above, the CEO can initiate a chat with the developer (dev), and the developer can respond in this chat. However, the developer cannot initiate a chat with the CEO. The developer can initiate a chat with the virtual assistant (va) and assign new tasks.

5. **Run Demo**: 
Run the demo to see your agents in action!

```python
agency.demo_gradio(height=900)
```

Terminal version:

```python
agency.run_demo()
```

6. **Get Completion**:
Get completion from the agency:

```python
completion_output = agency.get_completion("Please create a new website for our client.", yield_messages=False)
```

## Creating Agent Templates Locally (CLI)

This CLI command simplifies the process of creating a structured environment for each agent.

#### **Command Syntax:**

```bash
agency-swarm create-agent-template --name "AgentName" --description "Agent Description" [--path "/path/to/directory"] [--use_txt]
```

### Folder Structure

When you run the `create-agent-template` command, it creates the following folder structure for your agent:

```
/your-specified-path/
│
├── agency_manifesto.md or .txt # Agency's guiding principles (created if not exists)
└── AgentName/                  # Directory for the specific agent
    ├── files/                  # Directory for files that will be uploaded to openai
    ├── schemas/                # Directory for OpenAPI schemas to be converted into tools
    ├── AgentName.py            # The main agent class file
    ├── __init__.py             # Initializes the agent folder as a Python package
    ├── instructions.md or .txt # Instruction document for the agent
    └── tools.py                # Custom tools specific to the agent
    
```

This structure ensures that each agent has its dedicated space with all necessary files to start working on its specific tasks. The `tools.py` can be customized to include tools and functionalities specific to the agent's role.

## Future Enhancements

- Asynchronous communication and task handling.
- Creation of agencies that can autonomously create other agencies.
- Inter-agency communication for a self-expanding system.

## Contributing

For details on how to contribute you agents and tools to Agency Swarm, please refer to the [Contributing Guide](CONTRIBUTING.md).

## License

Agency Swarm is open-source and licensed under [MIT](https://opensource.org/licenses/MIT).



## Need Help?

If you require assistance in creating custom agent swarms or have any specific queries related to Agency Swarm, feel free to reach out through my website: [vrsen.ai](https://vrsen.ai)


# About this variant
## Refactored AgencySwarm to include new features.

- Focused on refactoring the Thread data model. Introduced the concept of session, solved the message deadlock problem, and reserved an interface to archive historical session messages.
- Organize historical sessions according to task descriptions.
    - AS determines which recipient's thread should be added to continue the session with new messages from upstream.
    - At the end of each session (one question and one answer), the task description of the session is updated with the following details. the AS determines the session to which new messages should be added based on the task description.
    ```
    {
          "backgroud": "Extract the context of the task from the first message of session history and briefly summarize it in one sentence", 
          "task_content": "Define clear and specific criteria based solely on the first message that indicate the task content is complete, focusing on the direct deliverables or outcomes requested.", 
          "completion conditions": "Define clear and specific criteria based solely on the first message that indicate the task content is complete, focusing on the direct deliverables or outcomes requested.", 
          "existing results": "Extract and *qualitatively summarize the (intermediate) results that have been produced by this task from the session history, and output them as a bulleted list.", 
          "unknown results": "Based on the principle of the 'completion conditions' field, the (intermediate) results required by the task but not yet obtained are extracted from the session history and output as a bulleted list",
          "status": "Analyze from the session history and the results what is the task status according to the completion condition, e.g., completed, uncompleted, unable to complete, uncertained etc."
    }
    ```
    
- Thread CoW mechanism interface (not implemented)

## Summary of highlights of the current release (AgencySwarm's transformation gains)

- No loss of task specificity and goals observed during long task progress (> 2 hours).
- Better performance for "task" type sessions, thanks to categorizing sessions by content and updating the description of the task at the end of each session to keep it specific.
- The problem of assistant's expiring when a custom function times out is now well mitigated by adding the context of the failure as a new message and re-running the thread, with no side effects observed.
- The session form of the code expression, easy to later change to a multi-threaded version, that is, each session has a separate thread management

## Handling issues

- Due to the timeout of the call to the custom Funtion, the submission of the result of the Funtion execution fails, causing the RUN to enter the expired state.
    - However, since the current AssistantAPI does not support editing the RUN'step, this does not make it possible to do a breakout. So a compromise is to wrap the result of the function's execution as a cue word message appended to the Thread and then re-RUN.

# 中文说明 (Chinese version)
## 重构AgencySwarm，加入新特性

- 重点重构了 Thread 数据模型。引入了Session的概念，解决了消息死锁问题，预留出了将历史会话消息归档的接口。
- 将历史的Session按照任务描述分类组织
    - AS会判断上游的新消息应该加入哪个recipient‘s thread来继续会话。
    - 在每次会话结束（一问一答）后，会更新该会话的任务描述（task description)，该描述具体内容如下。AS判断新消息加入的会话也是根据任务描述来选择的。
    
    ```
    {
          "backgroud": "Extract the context of the task from the first message of session history and briefly summarize it in one sentence", 
          "task_content": "Define clear and specific criteria based solely on the first message that indicate the task content is complete, focusing on the direct deliverables or outcomes requested.", 
          "completion conditions": "Define clear and specific criteria based solely on the first message that indicate the task content is complete, focusing on the direct deliverables or outcomes requested.", 
          "existing results": "Extract and *qualitatively summarize the (intermediate) results that have been produced by this task from the session history, and output them as a bulleted list.", 
          "unknown results": "Based on the principle of the 'completion conditions' field, the (intermediate) results required by the task but not yet obtained are extracted from the session history and output as a bulleted list",
          "status": "Analyze from the session history and the results what is the task status according to the completion condition, e.g., completed, uncompleted, unable to complete, uncertained etc."
    }
    ```
    
- Thread CoW机制接口（未实现）

## 当前版本亮点汇总（AgencySwarm的改造收益）

- 在长时间任务推进中，观测到任务的具体性和目标并没有减弱（> 2 hours）
- 针对”任务（task）“类型的会话有较好的表现，这得益于按内容内容分类会话，以及每次会话结束后对任务更新描述，保持任务的具体性。
- 当自定义函数超时后导致assistant’s expired问题目前有很好的缓解，将失败时候的上下文以新消息的形式加入并重新运行thread，观察到并没有副作用。
- Session形式的代码表达，便于后面改成多线程版本，即每个session有单独线程管理

## 处理issues

- 由于调用自定义Funtion超时后，Funtion执行结果提交失败，导致RUN进入expired状态。
    - 但由于目前AssistantAPI不支持编辑RUN’step，这就无法做到断点续传。因此一个妥协的办法是将函数的执行结果包装成提示词消息追加到Thread中，然后re-RUN。
