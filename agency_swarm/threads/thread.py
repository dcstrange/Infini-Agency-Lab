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
    instruction: str = None
    topic: str = None
    summary: str = None
    in_message_chain: str = None
    status: ThreadStatus = ThreadStatus.Ready
    properties: ThreadProperty = ThreadProperty.OneOff
    sessions = {} # {"recipient agent name", session}
    session_as_sender = None    # 用于python线程异常挂掉后的处理
    session_as_recipient= None # 用于python线程异常挂掉后的处理
    instruction: str = None
    
    def __init__(self, thread_id: str=None, copy_from=None):
        self.client = get_openai_client()
        if thread_id:
            self.thread_id = thread_id
            self.openai_thread = self.client.beta.threads.retrieve(self.thread_id)
        else:
            self.openai_thread = self.client.beta.threads.create()
            self.thread_id = self.openai_thread.id
        if copy_from is not None:
            # TODO: copy all message from a existed thread
            pass

    def _dump_info(self):
        pass