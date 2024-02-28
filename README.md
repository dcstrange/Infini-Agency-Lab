# Infini-Agency Lab

![poster](./figures/poster.png)

## 概述

**Infini-Agency Lab** 是专为Agency开发与优化而打造的先进框架工程。我们提供了一整套强大的工具和组件，旨在简化和加速Agency应用的构建与优化过程，使得定制和扩展Agency变得前所未有的简单。

## 核心特性

为了支持业务场景的Agency开发与调教，本课题核心焦点是研究与开发强大的底层框架，**提供丰富的能力组件**使开发人员更容易的构建自己需要的Agency，同时可以提供Tips给出开发和调优建议。这包括（不断追加）：

- **多场景对话支持**：覆盖任务分发、群讨论决策、内容生成等多种场景，提供灵活的对话处理能力。
- **模块化数据模型**：便于管理和扩展的按话题分类数据模型。
- **记忆归档与检索**：强大的记忆功能，轻松归档与检索所需信息。
- **任务质量监控**：引入先进的任务质量跟踪机制，确保任务执行的高效率。
- **可插拔Function设计**：支持自定义功能扩展，满足多样化业务需求。
- **高效日志系统**：强大的日志支持，简化开发与调试过程。



## 说明

本项目基于[agency-swarm](https://github.com/VRSEN/agency-swarm)二次开发



## 中文说明 (Chinese version)
### 重构AgencySwarm，加入新特性

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

### 当前版本亮点汇总（AgencySwarm的改造收益）

- 在长时间任务推进中，观测到任务的具体性和目标并没有减弱（> 2 hours）
- 针对”任务（task）“类型的会话有较好的表现，这得益于按内容内容分类会话，以及每次会话结束后对任务更新描述，保持任务的具体性。
- 当自定义函数超时后导致assistant’s expired问题目前有很好的缓解，将失败时候的上下文以新消息的形式加入并重新运行thread，观察到并没有副作用。
- Session形式的代码表达，便于后面改成多线程版本，即每个session有单独线程管理

### 处理issues

- 由于调用自定义Funtion超时后，Funtion执行结果提交失败，导致RUN进入expired状态。
    - 但由于目前AssistantAPI不支持编辑RUN’step，这就无法做到断点续传。因此一个妥协的办法是将函数的执行结果包装成提示词消息追加到Thread中，然后re-RUN。



## 待解决底层机制和框架工程问题

### 🔥High Priority

- [ ] 🔥🔥支撑更丰富对话类型

  - 自定义更多功能的SendMessage函数。当前SendMessage函数属于通用内同CoT的提示词。但针对不同类型对话，使用自定义的SendMessage可能会更好。当前所有的会话类型都是“任务规划和执行”。

  - 当前Agency-Swarm框架中Agent间沟通的**目的**是“问答”（且单向），这种单一目的的交流方式限制了Agency任务能力。后续考虑在Agency-Swarm底层追加其他目的形式的沟通方式，例如某个Agent有自己的主线任务，它通过其它Agent那里获取消息来不断思考自己的任务。

  - Agent Wait preparation机制。例如Team Leader需要等待并汇总（根据某个任务列表）所有Experts的任务意见后，再定夺下一步行动。这样的决策质量可能会更高，降低由于信息不全导致的决策失误。这个功能由Assistant并行调用SendMessage即可实现。

  - 发起多个Agents共同参与的会话。(目前还未有这种需求场景)。考虑，基于Assistant.Thread添加多人会话机制，重点是消息内容（比如要显示角色名称），消息处理方式，讨论方式。

  - 添加Waiting机制，`SendMeassage_Waiting_for(for_what, response_to_whom)`

    - 该机制用于构建无需回溯的任务图DAG，以减少由于回溯导致的消息传递冗余，增加任务推进清晰度。

      ![TaskGragh_DAG](C:/Users/fei19_vysxm3p/Documents/Workstation/Git/DBMA/figures/TaskGragh_DAG.png)

- [ ] 🔥支持MA架构的灵活性（flexibility），比如可插拔，可变换拓扑形态（未遇到该需求）

### 🧊Low Priority

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

### ✅Finished

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





## About this variant

### Refactored AgencySwarm to include new features.

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

### Summary of highlights of the current release (AgencySwarm's transformation gains)

- No loss of task specificity and goals observed during long task progress (> 2 hours).
- Better performance for "task" type sessions, thanks to categorizing sessions by content and updating the description of the task at the end of each session to keep it specific.
- The problem of assistant's expiring when a custom function times out is now well mitigated by adding the context of the failure as a new message and re-running the thread, with no side effects observed.
- The session form of the code expression, easy to later change to a multi-threaded version, that is, each session has a separate thread management

### Handling issues

- Due to the timeout of the call to the custom Funtion, the submission of the result of the Funtion execution fails, causing the RUN to enter the expired state.
  - However, since the current AssistantAPI does not support editing the RUN'step, this does not make it possible to do a breakout. So a compromise is to wrap the result of the function's execution as a cue word message appended to the Thread and then re-RUN.
