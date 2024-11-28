from agency_swarm import set_openai_key, Agent, Agency, AgencyEventHandler, get_openai_client
def get_my_openai_key():
    import json
    try:
        with open("C:/Users/fei19_vysxm3p/Documents/Workstation/Git/Infini-Agency-Lab/MyConfig.json", 'r') as f:
            config = json.load(f)
            return config['openai']['api_key']
    except FileNotFoundError:
        print("配置文件不存在")
        return None
    except KeyError:
        print("配置文件格式错误")
        return None

set_openai_key(get_my_openai_key())

from test_agents.AKSK import AKSK
agent1 = AKSK()

agency = Agency([
            agent1
            ],
            shared_instructions="This is a shared instruction",
            temperature=0,
        )

# print(agency.get_completion("请获取AK/SK"))

print(agency.get_completion("今天天气怎么样？"))