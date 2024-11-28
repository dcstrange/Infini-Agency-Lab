from agency_swarm.tools import BaseTool
from pydantic import Field
import os
import requests
from .APIGW_python_sdk_2_0_5.apig_sdk import signer

account_id = "MY_ACCOUNT_ID"
api_key = os.getenv("MY_API_KEY") # or access_token = os.getenv("MY_ACCESS_TOKEN")

class REST_API_Requset(BaseTool):
    """
    负责发送RESTful API请求，并返回请求相应信息。调用此函数前必须确认：1）以获得完整的可请求的API信息；2）获得access_key和secret_key
    """

    # Define the fields with descriptions using Pydantic Field
    method: str = Field(
        ..., description="HTTP请求方法，表示正在请求什么类型的操作。只能是以下选项中的一个：PUT/GET/POST/DELETE/HEAD/PATCH"
    )
    
    url: str = Field(
        ..., description="API请求的URI"
    )
    headers: str = Field(default=None,
                         description="默认为空"
    )    
    body: str = Field(
        ..., description="该部分可选。请求消息体通常以JSON结构化格式发出。"
    )   
    
    access_key: str = Field(
        ..., description="已经获取的access_key"
    )   
    secret_key: str = Field(
        ..., description="已经获取的secret_key"
    )   

    def run(self):
        sig = signer.Signer()
        sig.Key = self.access_key
        sig.Secret = self.secret_key
        
        r = signer.HttpRequest(self.method, self.url)
        r.headers = {"content-type": "application/json"}
        r.body = self.body
        
        try:
            sig.Sign(r)
        except Exception as e:
            print(str(e))
        resp = requests.request(r.method, r.scheme + "://" + r.host + r.uri, headers=r.headers, data=r.body)
        return f"响应码：{resp.status_code}\n, 响应原因：{resp.reason}\n, 响应内容：{resp.content}"
