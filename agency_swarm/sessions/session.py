import inspect
import time
from typing import Literal

from agency_swarm.threads import Thread
from agency_swarm.threads import ThreadStatus
from agency_swarm.threads import ThreadProperty

from agency_swarm.agents import Agent
from agency_swarm.messages import MessageOutput
from agency_swarm.user import User
from agency_swarm.util.oai import get_openai_client

class Session:
    caller_thread: Thread = None
    recipient_threads = []
    
    def __init__(self, caller_agent: Literal[Agent, User], recipient_agent: Agent):
        self.caller_agent = caller_agent
        self.recipient_agent = recipient_agent
        self.client = get_openai_client()
        if not self.caller_thread:
            self.caller_thread = Thread()
            
    def get_completion(self, 
                       message:str, 
                       message_files=None, 
                       topic: str=None,
                       yield_messages=True):
        """
        TODO: 在多线程版本中，该函数会在新的Python中执行，需要加锁，函数内部会修改recipient_threads[]对象
        """
        recipient = None
        if topic:
            #需要与已有主题的thread对话
            recipient = self._retrieve_topic_thread(topic)

        if recipient is None:
            # 如果不需要与已有主题的thread对话
            recipient = Thread()
            self.recipient_threads.append(recipient)
            recipient.assistant_id = self.recipient_agent.assistant.id
            if topic is not None: # New topic thread
                recipient.topic = topic
                recipient.properties = ThreadProperty.Persist
                # ... todo: cow....
            else:
                recipient.properties = ThreadProperty.OneOff
                
        recipient.in_message_chain = self.caller_thread.in_message_chain
        recipient.status = ThreadStatus.Running

        gen = self._get_completion_from_thread(recipient, message, message_files,yield_messages)
        try:
            while True:
                msg = next(gen)
                msg.cprint()
        except StopIteration as e:
            pass
            # print(f"@@@@ DEBUG: Block Here!!{e.value}")
            # # while True:
            # time.sleep(5)
            # # TODO:check是否recipient thread有更新消息
        except Exception as e: # 当会话超时，不能释放Thread对象
            print(f"Exception{inspect.currentframe().f_code.co_name}：{str(e)}")
            raise e
        
        # 成功得到recipient回复后
        recipient.status = ThreadStatus.Ready
        recipient.in_message_chain = None
        if recipient.properties is ThreadProperty.OneOff:
            self.recipient_threads.remove(recipient)
            recipient = None
        elif recipient.properties is ThreadProperty.Persist:
            pass
        elif recipient.properties is ThreadProperty.CoW:
            pass



    def _get_completion_from_thread(self, recipien_thread: Thread, message: str, message_files=None, yield_messages=True):

        # Determine the sender's name based on the agent type
        sender_name = "user" if isinstance(self.caller_agent, User) else self.caller_agent.name
        playground_url = f'https://platform.openai.com/playground?assistant={self.recipient_agent._assistant.id}&mode=assistant&thread={recipien_thread.thread_id}'
        print(f'THREAD:[ {sender_name} -> {self.recipient_agent.name} ]: URL {playground_url}')

        # send message
        self.client.beta.threads.messages.create(
            thread_id=recipien_thread.thread_id,
            role="user",
            content=message,
            file_ids=message_files if message_files else [],
        )

        if yield_messages:
            yield MessageOutput("text", self.caller_agent.name, self.recipient_agent.name, message)

        # create run
        run = self.client.beta.threads.runs.create(
            thread_id=recipien_thread.thread_id,
            assistant_id=self. recipient_agent.id,
        )
        
        while True:
            # wait until run completes
            while run.status in ['queued', 'in_progress']:
                time.sleep(5)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=recipien_thread.thread_id,
                    run_id=run.id
                )
                print(f"Run [{run.id}] Status: {run.status}")

            # function execution
            if run.status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []
                for tool_call in tool_calls:
                    if yield_messages:
                        yield MessageOutput("function", self.recipient_agent.name, self.caller_agent.name,
                                            str(tool_call.function))
                    
                    # TODO:这里如果是SendMessage函数，后续会采用创建新Python线程来执行，需要修改处理逻辑。
                    output = self._execute_tool(tool_call)
                    if inspect.isgenerator(output):
                        try:
                            while True:
                                item = next(output) # 可能会抛出超时异常(Error Code: 400)
                                if isinstance(item, MessageOutput) and yield_messages:
                                    yield item
                        except StopIteration as e:
                            output = e.value
                            print(output)
                        except Exception as e:
                            print(f"Exception{inspect.currentframe().f_code.co_name}：{str(e)}")
                            raise e
                    else:
                        if yield_messages:
                            yield MessageOutput("function_output", tool_call.function.name, self.recipient_agent.name,
                                                output)

                    tool_outputs.append({"tool_call_id": tool_call.id, "output": str(output)})

                # submit tool outputs
                run = self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=recipien_thread.thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
            # error
            elif run.status == "failed":
                raise Exception("Run Failed. Error: ", run.last_error)
            # return assistant message
            else:
                messages = self.client.beta.threads.messages.list(
                    thread_id=recipien_thread.thread_id
                )
                message = messages.data[0].content[0].text.value

                if yield_messages:
                    yield MessageOutput("text", self.recipient_agent.name, self.caller_agent.name, message)

                return message

    def _retrieve_topic_thread(self, topic:str) -> Thread:
        if not self.recipient_threads:
            return None
        else: # retrieve the thread with the topic. 
            for recipient in self.recipient_threads:
                if self._is_topic_related(recipient, topic) and recipient.status == ThreadStatus.Ready:
                    return recipient
        return None
                

    def _is_topic_related(self, recipient_thread: Thread, topic: str) -> bool:
        return recipient_thread.topic ==  topic


# Example usage within this file
if __name__ == "__main__":
    from agency_swarm import set_openai_key
    from getpass import getpass
    set_openai_key(getpass("Please enter your openai key: "))

    agent1 = Agent(name="agent1",
                     tools=None,
                     description="description",
                     instructions="description",
                     files_folder=None)
    agent2 = Agent(name="agent2",
                     tools=None,
                     description="description",
                     instructions="description",
                     files_folder=None)
    agent1.init_oai()
    agent2.init_oai()
    session = Session(agent1, agent2)
    session.get_completion("hello world.")
    
