import inspect
import json
import os
import queue
import threading
import uuid
from enum import Enum
from typing import List, Type, TypedDict, Callable, Any, Dict, Literal, Union

from openai.types.beta.threads.runs import RunStep
from pydantic import Field, field_validator, model_validator
from rich.console import Console
from typing_extensions import override
from openai.types.beta.threads import Message

from agency_swarm.agents import Agent
from agency_swarm.sessions import Session
from agency_swarm.messages import MessageOutput
from agency_swarm.messages.message_output import MessageOutput
from agency_swarm.threads import Thread
from agency_swarm.tools import BaseTool
from agency_swarm.user import User

from agency_swarm.util.streaming import AgencyEventHandler
from agency_swarm.util.log_config import setup_logging 

logger = setup_logging()

console = Console()


class SettingsCallbacks(TypedDict):
    load: Callable[[], List[Dict]]
    save: Callable[[List[Dict]], Any]


class ThreadsCallbacks(TypedDict):
    load: Callable[[], Dict]
    save: Callable[[Dict], Any]


class Agency:
    SessionType = Session
    def __init__(self, 
                 agency_chart, 
                 shared_instructions="", 
                 shared_files=None
                 ):
        """
        Initializes the Agency object, setting up agents, sessions, and core functionalities.

        Parameters:
        agency_chart: The structure defining the hierarchy and interaction of agents within the agency.
        shared_instructions (str, optional): A path to a file containing shared instructions for all agents. Defaults to an empty string.

        This constructor initializes various components of the Agency, including CEO, agents, sessions, and user interactions. It parses the agency chart to set up the organizational structure and initializes the messaging tools, agents, and sessions necessary for the operation of the agency. Additionally, it prepares a user entrance session for user interactions.
        """
        self.ceo = None
        self.agents:list[Agent] = []
        self.agents_and_sessions = {}
        self.shared_files = shared_files if shared_files else []

        if os.path.isfile(os.path.join(self.get_class_folder_path(), shared_instructions)):
            self._read_instructions(os.path.join(self.get_class_folder_path(), shared_instructions))
        elif os.path.isfile(shared_instructions):
            self._read_instructions(shared_instructions)
        else:
            self.shared_instructions = shared_instructions

        self._parse_agency_chart(agency_chart)
        self._create_send_message_tools()
        self._init_agents()
        #self._init_sessions() // No need to init sessions, cuz it is created dynamically in tasks. 

        self.user = User()
        self.entrance_session = Session(self.user, self.ceo)

    def get_completion(self, message: str, 
                       message_files=None, 
                       attachments: List[dict] = None,
                       yield_messages=True):
        """
        Retrieves the completion for a given message from the user entrance session.

        Parameters:
        message (str): The message for which completion is to be retrieved.
        message_files (list, optional): A list of file ids to be sent as attachments with the message. Defaults to None.
        yield_messages (bool, optional): Flag to determine if intermediate messages should be yielded. Defaults to True.

        Returns:
        Generator or final response: Depending on the 'yield_messages' flag, this method returns either a generator yielding intermediate messages or the final response from the entrance session.
        """
        gen = self.entrance_session.get_completion(message=message, 
                                                   message_files=message_files, 
                                                   attachments=attachments, 
                                                   is_persist=True, 
                                                   yield_messages=yield_messages)
        if not yield_messages:
            while True:
                try:
                    next(gen)
                except StopIteration as e:
                    return e.value

        return gen

    def get_completion_stream(self, 
                              message: str, 
                             event_handler: type(AgencyEventHandler),
                             message_files: List[str],
                             recipient_agent: Agent=None,
                             attachments: List[dict] = None):
        """
        Generates a stream of completions for a given message from the main thread.

        Parameters:
            message (str): The message for which completion is to be retrieved.
            event_handler (type(AgencyEventHandler)): The event handler class to handle the completion stream. https://github.com/openai/openai-python/blob/main/helpers.md
            message_files (list, optional): A list of file ids to be sent as attachments with the message. When using this parameter, files will be assigned both to file_search and code_interpreter tools if available. It is recommended to assign files to the most sutiable tool manually, using the attachments parameter.  Defaults to None.
        Returns:
            Final response: Final response from the main thread.
        """
        if not inspect.isclass(event_handler):
            raise Exception("Event handler must not be an instance.")
        
        res = self.entrance_session.get_completion_stream(
            message=message,
            event_handler=event_handler,
            message_files=message_files,
            recipient_agent = recipient_agent,
            attachments=attachments,
            is_persist=True
        )

        while True:
            try:
                next(res)
            except StopIteration as e:
                event_handler.on_all_streams_end()
                return e.value
         

    def demo_gradio(self, height=450, dark_mode=True):
        """
        Launches a Gradio-based demo interface for the agency chatbot.

        Parameters:
            height (int, optional): The height of the chatbot widget in the Gradio interface. Default is 600.
            dark_mode (bool, optional): Flag to determine if the interface should be displayed in dark mode. Default is True.
            share (bool, optional): Flag to determine if the interface should be shared publicly. Default is False.
        This method sets up and runs a Gradio interface, allowing users to interact with the agency's chatbot. It includes a text input for the user's messages and a chatbot interface for displaying the conversation. The method handles user input and chatbot responses, updating the interface dynamically.
        """
        try:
            import gradio as gr
        except ImportError:
            raise Exception("Please install gradio: pip install gradio")

        js = """function () {
          gradioURL = window.location.href
          if (!gradioURL.endsWith('?__theme={theme}')) {
            window.location.replace(gradioURL + '?__theme={theme}');
          }
        }"""
        # 切换主题模式
        if dark_mode:
            js = js.replace("{theme}", "dark")
        else:
            js = js.replace("{theme}", "light")

        message_file_ids = []   # 所有文件的id
        message_file_names = None
        # recipient_agents = [agent.name for agent in self.main_recipients]
        recipient_agent = self.ceo
        with gr.Blocks(js=js) as demo:
            chatbot_queue = queue.Queue()
            chatbot = gr.Chatbot(height=height)
            with gr.Row():
                with gr.Column(scale=9):
                    # dropdown = gr.Dropdown(label="Recipient Agent", choices=recipient_agents,
                    #                        value=recipient_agent.name)
                    msg = gr.Textbox(label="Your Message", lines=4)
                with gr.Column(scale=1):
                    file_upload = gr.Files(label="Files", type="filepath")
            button = gr.Button(value="Send", variant="primary")

            # def handle_dropdown_change(selected_option):
            #     nonlocal recipient_agent
            #     recipient_agent = self.get_agent_by_name(selected_option)

            def handle_file_upload(file_list):
                nonlocal message_file_ids
                nonlocal message_file_names
                message_file_ids = []
                message_file_names = []
                if file_list:
                    try:
                        for file_obj in file_list:
                            with open(file_obj.name, 'rb') as f:
                                # Upload the file to OpenAI
                                file = self.entrance_session.client.files.create(
                                    file=f,
                                    purpose="assistants"
                                )
                            message_file_ids.append(file.id)
                            message_file_names.append(file.filename)
                            print(f"Uploaded file ID: {file.id}")
                        return message_file_ids
                    except Exception as e:
                        print(f"Error: {e}")
                        return str(e)

                return "No files uploaded"

            def user(user_message, history):
                nonlocal recipient_agent
                if history is None:
                    history = []

                original_user_message = user_message

                if recipient_agent:
                    user_message = f"👤 User 🗣️ @{recipient_agent.name}:\n" + user_message.strip()
                else:
                    user_message = f"👤 User:" + user_message.strip()
                nonlocal message_file_names
                if message_file_names:
                    user_message += "\n\n📎 Files:\n" + "\n".join(message_file_names)

                return original_user_message, history + [[user_message, None]]

            class GradioEventHandler(AgencyEventHandler):
                message_output = None

                @override
                def on_message_created(self, message: Message) -> None:
                    if message.role == "user":
                        self.message_output = MessageOutput("text", self.agent_name, self.recipient_agent_name,
                                                            +message.content[0].text.value)

                    else:
                        self.message_output = MessageOutput("text", self.recipient_agent_name, self.agent_name,
                                                            "")

                    chatbot_queue.put("[new_message]")
                    chatbot_queue.put("mc:"+self.message_output.get_formatted_content())

                @override
                def on_text_delta(self, delta, snapshot):
                    chatbot_queue.put(delta.value)

                @override
                def on_tool_call_created(self, tool_call):
                    # TODO: add support for code interpreter and retirieval tools
                    if tool_call.type == "function":
                        chatbot_queue.put("[new_message]")
                        self.message_output = MessageOutput("function", self.recipient_agent_name, self.agent_name,
                                                            str(tool_call.function))
                        chatbot_queue.put("tcc:"+self.message_output.get_formatted_header() + "\n")

                @override
                def on_tool_call_done(self, snapshot):
                    self.message_output = None

                    # TODO: add support for code interpreter and retirieval tools
                    if snapshot.type != "function":
                        return

                    chatbot_queue.put(str(snapshot.function))

                    if snapshot.function.name == "SendMessage":
                        try:
                            args = eval(snapshot.function.arguments)
                            recipient = args["recipient"]
                            self.message_output = MessageOutput("text", self.recipient_agent_name, recipient,
                                                                args["message"])

                            chatbot_queue.put("[new_message]")
                            chatbot_queue.put("tcd:"+self.message_output.get_formatted_content())
                        except Exception as e:
                            pass

                    self.message_output = None

                @override
                def on_run_step_done(self, run_step: RunStep) -> None:
                    if run_step.type == "tool_calls":
                        for tool_call in run_step.step_details.tool_calls:
                            if tool_call.type != "function":
                                continue

                            if tool_call.function.name == "SendMessage":
                                continue

                            self.message_output = None
                            chatbot_queue.put("[new_message]")

                            self.message_output = MessageOutput("function_output", tool_call.function.name,
                                                                self.recipient_agent_name,
                                                                +tool_call.function.output)

                            chatbot_queue.put(self.message_output.get_formatted_header() + "\n")
                            chatbot_queue.put("rsd:"+tool_call.function.output)

                @override
                @classmethod
                def on_all_streams_end(cls):
                    cls.message_output = None
                    chatbot_queue.put("[end]")


            def bot(original_message, history):
                nonlocal message_file_ids
                nonlocal message_file_names
                nonlocal recipient_agent
                if message_file_ids:
                    print("Message files: ", message_file_ids)
                # Replace this with your actual chatbot logic
          
                completion_thread = threading.Thread(target=self.get_completion_stream, args=(
                    original_message, GradioEventHandler, message_file_ids,recipient_agent))
                completion_thread.start()                
                
                message_file_ids = []
                message_file_names = []

                new_message = True
                while True:
                    try:
                        bot_message = chatbot_queue.get(block=True)

                        if bot_message == "[end]":
                            completion_thread.join()
                            break

                        if bot_message == "[new_message]":
                            new_message = True
                            continue

                        if new_message:
                            history.append([None, bot_message])
                            new_message = False
                        else:
                            history[-1][1] += bot_message

                        yield "", history                    
                    except queue.Empty:
                        break

            button.click(
                user,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot]
            ).then(
                bot, [msg, chatbot], [msg, chatbot]
            )
            #dropdown.change(handle_dropdown_change, dropdown)
            file_upload.change(handle_file_upload, file_upload)
            msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
                bot, [msg, chatbot], [msg, chatbot]
            )
            # msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
            #     bot, chatbot, chatbot
            # )

            # Enable queuing for streaming intermediate outputs
            demo.queue()

        # Launch the demo
        demo.launch()
        return demo

    def run_demo(self):
        """
        Runs a demonstration of the agency's capabilities in an interactive command line interface.

        This function continuously prompts the user for input and displays responses from the agency's entrance session. It leverages the generator pattern for asynchronous message processing.

        Output:
        Outputs the responses from the agency's entrance session to the command line.
        """
        while True:
            console.rule()
            text = input("USER: ")

            try:
                gen = self.entrance_session.get_completion(message=text)
                while True:
                    message = next(gen)
                    message.cprint()
            except StopIteration as e:
                pass

    def _parse_agency_chart(self, agency_chart):
        """
        Parses the provided agency chart to initialize and organize agents within the agency.

        Parameters:
        agency_chart: A structure representing the hierarchical organization of agents within the agency.
                    It can contain Agent objects and lists of Agent objects.

        This method iterates through each node in the agency chart. If a node is an Agent, it is set as the CEO if not already assigned.
        If a node is a list, it iterates through the agents in the list, adding them to the agency and establishing communication
        sessions between them. It raises an exception if the agency chart is invalid or if multiple CEOs are defined.
        """
        if not isinstance(agency_chart, list):
            raise Exception("Invalid agency chart.")

        if len(agency_chart) == 0:
            raise Exception("Agency chart cannot be empty.")

        for node in agency_chart:
            if isinstance(node, Agent):
                if self.ceo:
                    raise Exception("Only 1 ceo is supported for now.")
                self.ceo = node
                self._add_agent(self.ceo)

            elif isinstance(node, list):
                for i, agent in enumerate(node):
                    if not isinstance(agent, Agent):
                        raise Exception("Invalid agency chart.")

                    index = self._add_agent(agent)

                    if i == len(node) - 1:
                        continue

                    if agent.name not in self.agents_and_sessions.keys():
                        self.agents_and_sessions[agent.name] = {}

                    for other_agent in node:
                        # agent之间在同一个list可以相互通信
                        if other_agent.name == agent.name:
                            continue
                        if other_agent.name not in self.agents_and_sessions[agent.name].keys():
                            self.agents_and_sessions[agent.name][other_agent.name] = {
                                "agent": agent.name,
                                "recipient_agent": other_agent.name,
                            }

            else:
                raise Exception("Invalid agency chart.")

    def _add_agent(self, agent):
        """
        Adds an agent to the agency, assigning a temporary ID if necessary.

        Parameters:
        agent (Agent): The agent to be added to the agency.

        Returns:
        int: The index of the added agent within the agency's agents list.

        This method adds an agent to the agency's list of agents. If the agent does not have an ID, it assigns a temporary unique ID. It checks for uniqueness of the agent's name before addition. The method returns the index of the agent in the agency's agents list, which is used for referencing the agent within the agency.
        """
        if not agent.id:
            # assign temp id
            agent.id = "temp_id_" + str(uuid.uuid4())
        if agent.id not in self.get_agent_ids():
            if agent.name in self.get_agent_names():
                raise Exception("Agent names must be unique.")
            self.agents.append(agent)
            return len(self.agents) - 1
        else:
            return self.get_agent_ids().index(agent.id)


    def _read_instructions(self, path):
        """
        Reads shared instructions from a specified file and stores them in the agency.

        Parameters:
        path (str): The file path from which to read the shared instructions.

        This method opens the file located at the given path, reads its contents, and stores these contents in the 'shared_instructions' attribute of the agency. This is used to provide common guidelines or instructions to all agents within the agency.
        """
        path = path
        with open(path, 'r') as f:
            self.shared_instructions = f.read()

    def plot_agency_chart(self):
        pass

    def _create_send_message_tools(self):
        """
        Creates and assigns 'SendMessage' tools to each agent based on the agency's structure.

        This method iterates through the agents and sessions in the agency, creating SendMessage tools for each agent. 
        These tools enable agents to send messages to other agents as defined in the agency's structure. 
        The SendMessage tools are tailored to the specific recipient agents that each agent can communicate with.

        No input parameters.

        No output parameters; this method modifies the agents' toolset internally.
        """
        for agent_name, sessions in self.agents_and_sessions.items():
            recipient_names = list(sessions.keys())
            recipient_agents = self.get_agents_by_names(recipient_names)
            agent = self.get_agent_by_name(agent_name)
            agent.add_tool(self._create_send_message_tool(agent, recipient_agents))

    def _create_send_message_tool(self, agent: Agent, recipient_agents: List[Agent]):
        """
        Creates a SendMessage tool to enable an agent to send messages to specified recipient agents.

        Parameters:
        agent (Agent): The agent who will be sending messages.
        recipient_agents (List[Agent]): A list of recipient agents who can receive messages.

        Returns:
        SendMessage: A SendMessage tool class that is dynamically created and configured for the given agent and its recipient agents. 
        This tool allows the agent to send messages to the specified recipients, facilitating inter-agent communication within the agency.
        """
        recipient_names = [agent.name for agent in recipient_agents]
        recipients = Enum("recipient", {name: name for name in recipient_names})

        agent_descriptions = ""
        for recipient_agent in recipient_agents:
            if not recipient_agent.description:
                continue
            agent_descriptions += recipient_agent.name + ": "
            agent_descriptions += recipient_agent.description + "\n"

        outer_self = self

        class SendMessage(BaseTool):
            """Use this tool to facilitate direct, synchronous communication between specialized agents within your agency.
              When you send a message using this tool, you receive a response exclusively from the designated recipient agent. 
              To continue the dialogue, invoke this tool again with the desired recipient and your follow-up message. Remember, 
              communication here is synchronous; the recipient agent won't perform any tasks post-response. 
              You are responsible for relaying the recipient agent's responses back to the user, as they do not have direct access to these replies.
              Keep engaging with the tool for continuous interaction until the task is fully resolved."""
            chain_of_thought: str = Field(...,
                                          description="Think step by step to determine the correct recipient and "
                                                      "message. For multi-step tasks, first break it down into smaller"
                                                      "steps. Then, determine the recipient and message for each step.")
            # chain_of_thought改为my_primary_instruction
            recipient: recipients = Field(..., description=agent_descriptions)
            message: str = Field(...,
                                 description="Specify the task required for the recipient agent to complete. Focus on "
                                             "clarifying what the task entails, rather than providing exact "
                                             "instructions.")
            message_files: List[str] = Field(default=None,
                                             description="A list of file ids to be sent as attachments to the message. Only use this if you have the file id that starts with 'file-'.",
                                             examples=["file-1234", "file-5678"])
            caller_agent_name: str = Field(default=agent.name,
                                           description="The agent calling this tool. Defaults to your name. Do not change it.")

            @field_validator('recipient')
            def check_recipient(cls, value):
                if value.value not in recipient_names:
                    raise ValueError(f"Recipient {value} is not valid. Valid recipients are: {recipient_names}")
                return value

            @field_validator('caller_agent_name')
            def check_caller_agent_name(cls, value):
                if value != agent.name:
                    raise ValueError(f"Caller agent name must be {agent.name}.")
                return value

            def run(self, caller_thread):
                if self.recipient.value in caller_thread.sessions.keys(): #如果已经有session，直接使用session
                    session = caller_thread.sessions[self.recipient.value]
                    info = f"Retrived Session: caller_agent={session.caller_agent.name}, recipient_agent={session.recipient_agent.name}"
                    logger.info(info)           
                else:
                    session = Session(caller_agent=self.caller_agent, # TODO: check this parameter if error.
                                      recipient_agent=outer_self.get_agent_by_name(self.recipient.value),
                                      caller_thread=caller_thread)
                    info = f"New Session Created! caller_agent={self.caller_agent.name}, recipient_agent={self.recipient.value}"
                    logger.info(info)
                    caller_thread.sessions[self.recipient.value] = session

                if not isinstance(session, Session):
                    raise Exception("error")                    
                
                #===================# python.thread.create()====================================
                # TODO: 创建新的Python线程执行session
                caller_thread.session_as_sender = session
                try:
                    message = session.get_completion(message=self.message, 
                                             message_files=self.message_files,
                                             event_handler=self.event_handler)
                except Exception as e:
                    logger.info(f"Exception{inspect.currentframe().f_code.co_name}：{str(e)}",exc_info=True)
                    raise e
                #======================# python.thread.wait_to_join()=================================
                
                return message or ""

        # TODO: 每个Agent有自己的SendMessage对象。但是当前这个版本认为一个Agent在某一时刻只能有一个SendMessage函数被调用。
        # 实际上，在Session模型中，一个Agent有多个Thread，因此可能会有多个SendMessage并行。所以需要注意全局变量的使用。
        return SendMessage 

    def get_agent_by_name(self, agent_name)->Agent:
        """
        Retrieves an agent from the agency based on the agent's name.

        Parameters:
        agent_name (str): The name of the agent to be retrieved.

        Returns:
        Agent: The agent object with the specified name.

        Raises:
        Exception: If no agent with the given name is found in the agency.
        """
        for agent in self.agents:
            if agent.name == agent_name:
                return agent
        raise Exception(f"Agent {agent_name} not found.")

    def get_agents_by_names(self, agent_names):
        """
        Retrieves a list of agent objects based on their names.

        Parameters:
        agent_names: A list of strings representing the names of the agents to be retrieved.

        Returns:
        A list of Agent objects corresponding to the given names.
        """
        return [self.get_agent_by_name(agent_name) for agent_name in agent_names]

    def get_agent_ids(self):
        """
        Retrieves the IDs of all agents currently in the agency.

        Returns:
        List[str]: A list containing the unique IDs of all agents.
        """
        return [agent.id for agent in self.agents]

    def get_agent_names(self):
        """
        Retrieves the names of all agents in the agency.

        Parameters:
        None

        Returns:
        List[str]: A list of names of all agents currently part of the agency.
        """
        return [agent.name for agent in self.agents]

    def get_recipient_names(self):
        """
        Retrieves the names of all agents in the agency.

        Returns:
        A list of strings, where each string is the name of an agent in the agency.
        """
        return [agent.name for agent in self.agents]

    def _init_agents(self):
        """
        Initializes all agents in the agency with unique IDs, shared instructions, and OpenAI models.

        This method iterates through each agent in the agency, assigns a unique ID, adds shared instructions, and initializes the OpenAI models for each agent.

        There are no input parameters.

        There are no output parameters as this method is used for internal initialization purposes within the Agency class.
        """
        for agent in self.agents:
            if "temp_id" in agent.id:
                agent.id = None
            agent.add_shared_instructions(self.shared_instructions)

            if self.shared_files:
                if isinstance(agent.files_folder, str):
                    agent.files_folder = [agent.files_folder]
                    agent.files_folder += self.shared_files
                elif isinstance(agent.files_folder, list):
                    agent.files_folder += self.shared_files

            agent.init_oai()

    # def _init_sessions(self):
    #     """
    #     Initializes sessions for communication between agents within the agency.

    #     This method creates Session objects for each pair of interacting agents as defined in the agents_and_sessions attribute of the Agency. Each session facilitates communication and task execution between an agent and its designated recipient agent.

    #     No input parameters.

    #     Output Parameters:
    #     This method does not return any value but updates the agents_and_sessions attribute with initialized Session objects.
    #     """
    #     for agent_name, sessions in self.agents_and_sessions.items():
    #         for other_agent, items in sessions.items():
    #             self.agents_and_sessions[agent_name][other_agent] = Session(self.get_agent_by_name(items["agent"]),
    #                                                                         self.get_agent_by_name(items["recipient_agent"]))

    def get_class_folder_path(self):
        """
        Retrieves the absolute path of the directory containing the class file.

        Returns:
        str: The absolute path of the directory where the class file is located.
        """
        return os.path.abspath(os.path.dirname(inspect.getfile(self.__class__)))
