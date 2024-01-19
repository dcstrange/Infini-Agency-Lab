import inspect
import time
from typing import Literal

from agency_swarm.agents import Agent
from agency_swarm.messages import MessageOutput
from agency_swarm.user import User
from agency_swarm.util.oai import get_openai_client

from enum import Enum

class ThreadStatus(Enum):
    Running = "Running"
    Ready = "Ready"

class ThreadProperty(Enum):
    Persist = "Persist"
    OneOff = "One-Off"
    CoW = "Copy on Write"


class Thread:
    thread_id: str = None
    openai_thread = None
    assistant_id: str = None
    instruction: str = None
    topic: str = None
    summary: str = None
    in_message_chain: str = None
    status: ThreadStatus = None
    properties: ThreadProperty = None

    def __init__(self, thread_id: str=None):
        self.client = get_openai_client()
        if thread_id:
            self.thread_id = thread_id
            self.openai_thread = self.client.beta.threads.retrieve(self.thread_id)
        else:
            self.openai_thread = self.client.beta.threads.create()
            self.thread_id = self.openai_thread.id

        def _dump_info(self):
            pass