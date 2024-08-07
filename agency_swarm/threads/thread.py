from litellm import SyncCursorPage
from openai.resources.beta.threads.messages import Message
from agency_swarm.util.oai import get_openai_client
from openai.types.beta.thread_create_params import Message as MessageParams
from typing import Iterable
from enum import Enum

class ThreadStatus(Enum):
    Running = "Running"
    Ready = "Ready"

class ThreadProperty(Enum):
    Persist = "Persist"
    OneOff = "One-Off"
    CoW = "Copy on Write" # 语言模型正在调用函数

class Thread:
    def __init__(self, thread_id: str=None, copy_from:'Thread' =None):
        self.client = get_openai_client()
        self.thread_id: str = thread_id
        self.openai_thread = None
        self.instruction: str = None
        self.in_message_chain: str = None
        self.status: ThreadStatus = ThreadStatus.Ready
        self.properties: ThreadProperty = ThreadProperty.Persist
        # self.sessions = {}                # eg: {"recipient agent name", session}
        self.session_as_sender = None     # 用于python线程异常挂掉后的处理
        self.session_as_recipient = None  # 用于python线程异常挂掉后的处理
        self.task_description = ""
        
        if self.thread_id:
            self.openai_thread = self.client.beta.threads.retrieve(self.thread_id)
        else:
            self.openai_thread = self.client.beta.threads.create()
            self.thread_id = self.openai_thread.id

        if copy_from is not None:
            # TODO: copy all message from a existed thread
            self.copy_thread(src=copy_from)

    def _dump_info(self):
        pass

    def copy_thread(self, src: 'Thread'):
        self.client = src.client
        self.instruction = src.instruction
        self.in_message_chain = src.in_message_chain
        self.status = ThreadStatus.Ready
        self.properties = src.properties
        self.task_description = src.task_description

        messages = self.client.beta.threads.messages.list(thread_id=src.thread_id, limit=100)
        tool_resources = self.client.beta.threads.retrieve(self.thread_id).tool_resources

        self.openai_thread = self.client.beta.threads.create(
            messages=self.convert_messages(messages.data),
            tool_resources=tool_resources,
        )
        self.thread_id = self.openai_thread.id

    def convert_messages(self, messages: list[Message]) -> Iterable[MessageParams]:
        for message in messages[::-1]:
            for content in message.content:
                yield MessageParams(
                    content=content.text.value,
                    role= message.role,
                    attachments=message.attachments,
                    metadata=message.metadata
                )
