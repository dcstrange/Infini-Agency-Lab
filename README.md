## 可以或需要新增的功能

* **Session**部分的继续完善：代码中有少部分未完成的点

* **对其他模型API的支持**：可选的方案是使用[astra-assistants]([datastax/astra-assistants-api: Drop in replacement for the OpenAI Assistants API (github.com)](https://github.com/datastax/astra-assistants-api))的服务，该项目调用[LiteLLM](https://github.com/BerriAI/litellm)的服务，将当前流行的模型都封装成`OpenAI`的assistant AI样式的接口，部分模型不支持streaming服务

  ```python
  import os
  import sys
  from pathlib import Path
  
  project_root = Path(__file__).parent.parent.parent.absolute()
  os.environ['AS_PROJECT_ROOT'] = str(project_root)
  
  from openai import OpenAI
  from astra_assistants import patch
  from agency_swarm.agency.agency import Agency
  from agency_swarm.agents.agent import Agent
  from agency_swarm.util.oai import set_openai_client
  from dotenv import load_dotenv
  
  load_dotenv(".env") # api_key之类的保存在.env文件中
  
  client = patch(OpenAI()) 
  # agency-swarm的client要修改，目前代码运行时只有一个client，无法同时支持多种模型
  
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
  
  agency.demo_gradio()
  ```

  

* **数据库环境**：利用语言模型搭建虚拟的数据库环境，或者编写脚本代码来提供访问使用真实数据库的能力

* **流式传输-事件处理器**：`OpenAI`推出了利用`event_handler`来处理API的各种响应的方式，可以在类中对消息统一处理，来代替一部分要专门去代码中响应位置处进行的修改

  ```python
  class GradioEventHandler(AgencyEventHandler):
  
      @override
      def on_message_created(self, message: Message) -> None:
     	 	# 在消息被创建的时候触发
      	pass
  
      @override
      def on_text_delta(self, delta, snapshot):
          # 所有的新消息，on_message_created负责添加消息头，该函数负责添加内容
          pass
  
      @override
      def on_tool_call_created(self, tool_call):
          # 工具调用时触发，比如SendMessage
          pass
  
      @override
      def on_tool_call_done(self, snapshot):
          # 这里主要是处理函数调用请求结束后，目前只处理SendMessage，显示发送的信息 
          pass
  
      @override
      def on_run_step_done(self, run_step: RunStep) -> None:
          pass
  
      @override
      @classmethod
      def on_all_streams_end(cls):
          pass
  ```

* **验证器**：`Agent`类提供了`response_validator`方法，其中可以加入一些措施对语言模型的回答进行验证，例如`llm_validator`等

* **置信度**：可以考虑为每个`Agent`的回答加上置信度，作为消息的一部分发送给其他`Agent`，以供他们进行决策，（1）具体可以通过提示词形式让`Agent`自行给出，（2）或者让一个专门的`Agent`来评估出置信度

* **限制讨论轮次**：解决问题时需要考虑一下迭代层数（讨论轮数），而不是讨论越深越好

  