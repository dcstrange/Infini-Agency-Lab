from agency_swarm.tools import BaseTool
from pydantic import Field
import os
import requests
from .APIGW_python_sdk_2_0_5.apig_sdk import signer

class API_Requset(BaseTool):
    """
    A brief description of what the custom tool does.
    The docstring should clearly explain the tool's purpose and functionality.
    It will be used by the agent to determine when to use this tool.
    """

    # Define the fields with descriptions using Pydantic Field
    method: str = Field(
        ..., description="API的请求方法，只能是如下之一：GET/PUT/POST/DELETE/FETCH"
    )
    
    url: str = Field(
        ..., description="API的请求URL"
    )
    
    header: str = Field(default=None, description="默认不填"
    )
    body: str = Field(
        ..., description="API的请求体"
    )
    
    access_key: str = Field(
        ..., description="access_key信息"
    )
    secret_key: str = Field(
        ..., description="secret_key信息"
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

