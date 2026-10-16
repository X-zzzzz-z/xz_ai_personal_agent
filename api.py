#py -3.13 -m uvicorn api:app --reload
"""
URL	Uniform Resource Locator，统一资源定位符	标明访问哪个地址、哪个资源，平时称为“网址”
HTTP	Hypertext Transfer Protocol，超文本传输协议	规定客户端和服务器如何交换请求、响应
FastAPI	一个 Python Web 框架	帮你编写接收请求、处理数据、返回响应的接口

状态码	含义	项目中的例子
200	请求处理成功	正常查询、问答返回
400	请求有问题	可以用来表示问题为空
404	找不到目标资源	访问没有登记的路径
422	请求数据校验失败	请求体缺少必填的 question
500	服务器内部错误	程序运行时发生未处理的异常

Request：请求。
Response：响应。
Headers：头部，携带格式等附加信息。
Body：正文，承载具体数据。

请求头	    表达的意思
Content-Type: application/json	我发送给服务器的请求体是 JSON
Accept: application/json	我希望服务器返回 JSON
"""

#/records 接收明确的查询条件；/chat 接收自然语言，由模型决定如何处理。

#GET /records：查询记录。
#POST /records：添加并保存记录。
#POST /chat：接收问题，调用 Agent，返回回答。
from pydantic import BaseModel
from learning_tools import query_learning_records
from learning_tools import add_learning_record
from fastapi.responses import JSONResponse
from fastapi import FastAPI
from agent import run_agent

app = FastAPI()         #创建应用对象

class ChatRequest(BaseModel):       #ChatRequest类：规定数据是怎么样的 request对象：保存提交的数据
    question: str
#登记处理规则
@app.post(
    "/chat",
    summary="向学习助手提问",       #summary：让 /docs 显示中文接口标题。
    responses={                     #responses：让 /docs 明确列出 400 及其说明。
        400: {"description": "问题为空或只包含空白字符"}
    }
)        
def chat_api(request: ChatRequest):         #接收ChatRequest解析的请求数据对象
    question = request.question.strip()     #取得问题，去掉首尾空白

    if not question:  
        return JSONResponse(
            status_code=400,
            content={
                "success":False,
                "message":"问题不能为空",
                "data": None
            }
        )      
    result = run_agent(question)
    return result

class LearningRecordRequest(BaseModel):   #BaseModel:Pydantic 提供的基础类，帮助解析和校验数据
    date: str
    title: str
    content: str
    key_points: str
    unresolved: str

#添加记录
@app.post("/records")       #接收请求
def create_record(record: LearningRecordRequest):       #将校验后的请求体保存到record
    result = add_learning_record(       #执行内部函数添加到json文件完成校验和保存
        date=record.date,
        title=record.title,
        content=record.content,
        key_points=record.key_points,
        unresolved=record.unresolved
    )
    return result

#登记规则：GET /health 请求由 health() 处理。
@app.get("/health")     #用于确认服务能响应
def health():
    return{"status": "ok"}

#查询记录
@app.get("/records")
def get_records(keyword: str = "",date: str = ""):
    result = query_learning_records(keyword=keyword,date=date)
    return result