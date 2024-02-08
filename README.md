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



# 待解决底层机制和框架工程问题

## 🔥High Priority

- [ ] 🔥🔥支撑更丰富对话类型

  - 自定义更多功能的SendMessage函数。当前SendMessage函数属于通用内同CoT的提示词。但针对不同类型对话，使用自定义的SendMessage可能会更好。当前所有的会话类型都是“任务规划和执行”。

  - 当前Agency-Swarm框架中Agent间沟通的**目的**是“问答”（且单向），这种单一目的的交流方式限制了Agency任务能力。后续考虑在Agency-Swarm底层追加其他目的形式的沟通方式，例如某个Agent有自己的主线任务，它通过其它Agent那里获取消息来不断思考自己的任务。

  - Agent Wait preparation机制。例如Team Leader需要等待并汇总（根据某个任务列表）所有Experts的任务意见后，再定夺下一步行动。这样的决策质量可能会更高，降低由于信息不全导致的决策失误。这个功能由Assistant并行调用SendMessage即可实现。

  - 发起多个Agents共同参与的会话。(目前还未有这种需求场景)。考虑，基于Assistant.Thread添加多人会话机制，重点是消息内容（比如要显示角色名称），消息处理方式，讨论方式。

  - 添加Waiting机制，`SendMeassage_Waiting_for(for_what, response_to_whom)`

    - 该机制用于构建无需回溯的任务图DAG，以减少由于回溯导致的消息传递冗余，增加任务推进清晰度。

      ![TaskGragh_DAG](C:/Users/fei19_vysxm3p/Documents/Workstation/Git/DBMA/figures/TaskGragh_DAG.png)

- [ ] 🔥支持MA架构的灵活性（flexibility），比如可插拔，可变换拓扑形态（未遇到该需求）

## 🧊Low Priority

- [ ] 将专家团Expert Team打包成另一个Agency，可能由Team Leader Agent作为对外接口。整个架构是由多个主题的Agencies组成。[重要不紧急]

- [ ] 添加自定义函数并发执行能力。OpenAI Assistant具备并行调用Functions能力，见[Parallel function calling](https://platform.openai.com/docs/guides/function-calling/parallel-function-calling)。在设计Agent时候需要在任务规划时候考虑到并行函数的能力。例如，Expert Team Leader可以将可以并行处理的任务同时发给三个不同的Experts，将他们返回的结果做后一步的处理。但如果不需要汇总他们的结果再做处理，则可以考虑创建新的Thread/session来并发发起任务。

- [ ] 增加单Agent的灵活性。考虑运行时自主修改（增删改）Assistant Instruction，可根据任务的执行状态自动优化Assistant和MA结构。(未遇到该需求，可能会产生在触发了某些特殊事件)

  - 参考👉 [Step 4: Run the Assistant](https://platform.openai.com/docs/assistants/overview/step-4-run-the-assistant)

    > You can [optionally pass new instructions](https://platform.openai.com/docs/api-reference/runs/createRun#runs-createrun-instructions) to the Assistant while creating the Run but note that these instructions override the default instructions of the Assistant.
    >
    > ```python
    > run = client.beta.threads.runs.create(
    > thread_id=thread.id,
    > assistant_id=assistant.id,
    > instructions="Please address the user as Jane Doe. The user has a premium account."
    > )
    > ```

## ✅Finished

- 实现伪DB交互环境
  - 实现在DBMA/db_pseudo_env目录中。包含着一个伪DB环境Web Server，和向伪DB环境发送任务消息的Client。使用命令`python db_pseudo_env/db_pseudu_env_server.py`启动伪DB环境Server，并访问 http://localhost:5000/task 查看任务并手动输入任务执行结果。
- 区分打印消息时候的"talk to"和“response to"的图标。当前版本统一用了🗣️表示。
- 解决由于Function call时间过长导致OpenAI会话过期。
  - 由于调用自定义Funtion超时后，Funtion执行结果提交失败，导致RUN进入expired状态。但由于目前AssistantAPI不支持编辑RUN’step，这就无法做到断点续传。因此我们妥协的解决方法是把函数的执行结果包装成提示词消息追加到Thread中，然后re-RUN。
- 打印所有运行时日志。日志目录存放在`os.environ['AS_PROJECT_ROOT']`指定的环境变量中（在本项目中`main.py`中定义）
- 添加Session对象，按照任务内容隔离Thread。目前AgencySwarm的Agent间交流机制是同步版本，从root agent (CEO) 开始，<u>递归的</u>调用相关Agent的SendMessage函数。虽然在AgencySwarm抽象出了CommunicationThread对象（见`agency_swarm\threads\thread.py`），即每个pair <sender agent, recipient agent> 所对应的上下文，但所有的Thread对象在单线程中被串行执行，而且消息回复仅仅是简单的function return。后面需要改成多线程，异步版本。备注：当前版本是通过`Thread._execute_tool(thread.self, self.recipient_agent.SendMessage())`来attach到新的CommunicationThread上下文的。

  - 修改思路：每个Agent的实现为一个系统线程，Agent实例包含着对应Assitant环境，和由self作为message Sender的所有会话（Session）。我们使用Session替换掉CommunicationThread，因为CommunicationThread对象实在单线程中被Agency全局管理，Session由Agent线程自己管理。这样消息发送/回复的机制就可以是REST接口了。
- 为后续出多线程版本预留开发位置（如果有必要的话）。
- AgencySwarm原始方案
  <img src="C:/Users/fei19_vysxm3p/Documents/Workstation/Git/DBMA/figures/tmp437D.png" alt="image-20231226143945843" style="zoom: 25%;" /> <img src="C:/Users/fei19_vysxm3p/Documents/Workstation/Git/DBMA/figures/tmpA15E.png" alt="image-20231226143945843" style="zoom: 25%;" />

