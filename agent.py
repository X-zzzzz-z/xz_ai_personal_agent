import json
import inspect
from llm import chat

SYSTEM_PROMPT = """
你是一个个人学习助手，可以使用工具添加学习记录、查询学习记录和搜索学习笔记。

同一个用户问题最多调用一次 semantic_search_notes，
不要使用不同说法重复搜索同一个问题。

当 semantic_search_notes 返回 data 为空时，不要再次调用该工具。
如果本轮只搜索了笔记，只说“当前可搜索的笔记中未找到足够相关内容”。
此时不要用模型自身知识补写答案，也不要声称查询过学习记录。
"""

def execute_tool(registry,tool_name: str,arguments: str):
    try:
        args = json.loads(arguments)
    except json.JSONDecodeError:
        return {
            "success": False,
            "message": "工具参数不是合法的JSON",
            "data": None
        }

    if not isinstance(args,dict):
        return {
            "success": False,
            "message": "工具参数必须是JSON对象",
            "data": None
        }

    try:
        tool_func = registry.get_tool(tool_name)
    except ValueError as error:
        return{
            "success": False,
            "message": str(error),
            "data": None
        }

    try:
        inspect.signature(tool_func).bind(**args)       #bind:试着把字典里的值放到函数参数位置上
    except TypeError as error:
        return{
            "success": False,
            "message": f"工具参数不匹配：{error}",
            "data": None
        }

    try:
        return tool_func(**args)
    except Exception as error:
        return{
            "success":False,
            "message":(f"工具执行失败：{type(error).__name__}:{error}"),
            "data":None
        }

    
def run_agent(user_input: str):
#循环前：接受问题、注册工具、构造消息
    from tool_registry import ToolRegistry
    from learning_tools import (
        add_learning_record,
        query_learning_records,
        semantic_search_notes
    )
#登记到注册表
    registry = ToolRegistry()
    registry.register(semantic_search_notes)
    registry.register(query_learning_records)
    registry.register(add_learning_record)
#问题放入消息
    messages = [
        {
            "role": "system", 
            "content": SYSTEM_PROMPT
            },
            {
                "role":"user",
                "content": user_input
            }
    ]

#循环中：请求模型、按模型响应执行工具、再反馈结果
    used_search_tools = set()
    for round_num in range(3):
        available_tools = registry.get_schema() if round_num < 2 else None
        try:
            message = chat(messages,tools=available_tools)
        except Exception as error:
            return {
                "success": False,
                "message": f"模型请求失败：{type(error).__name__}: {error}",
                "data": None
            }

        messages.append(message)
#返回位置：将最终回答或失败信息交给调用方
        if message.tool_calls:
            if round_num == 2:
                return {
                    "success": False,
                    "message": "已达到最多3次模型调用，仍有工具待调用，本轮未执行。",
                    "data": None
                }
            
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments = tool_call.function.arguments

                if (
                    tool_name in {"semantic_search_notes", "query_learning_records"}
                    and tool_name in used_search_tools
                ):
                    result = {
                        "success": False,
                        "message": f"已阻止重复调用搜索工具：{tool_name}",
                        "data": None
                    }
                else:
                    result = execute_tool(
                        registry,
                        tool_name,
                        arguments
                    )

                    if tool_name in {
                        "semantic_search_notes",
                        "query_learning_records"
                    }:
                        used_search_tools.add(tool_name)

                print(result["message"])

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })
        else:
            return {
                "success": True,
                "message": "问答完成",
                "data": {"answer": message.content}
            }
    return {
        "success": False,
        "message": "问答流程结束，未获得最终回答",
        "data": None
    }

if __name__ == "__main__":
    user_input = input("请输入你的问题：")
    result = run_agent(user_input)

    if result["success"]:
        print(result["data"]["answer"])
    else:
        print(result["message"])