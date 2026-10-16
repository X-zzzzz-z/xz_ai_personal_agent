"""
代码	数据放在哪里／做什么
params=query_params	把查询条件加入 URL
json=payload	把数据编码为 JSON 请求体
response.json()	把收到的 JSON 正文解析成 Python 数据
query_params：查询参数;query 是“查询”，params 是 parameters（参数）的缩写。
response：响应。这里保存服务器返回的响应对象，包含状态码、响应头和正文。
payload 要发送的数据；ConnectionError 的中文是“连接错误”。
check_health 是“检查服务健康状态”的意思
"""
import requests

def ask_agent():
    payload = {
        "question": "查询我关于FastAPI的学习记录"
    }

    try:
        response = requests.post(
            "http://127.0.0.1:8000/chat",
            json=payload,
            timeout=60
        )
    except requests.exceptions.Timeout:
        print("请求超时")
        return
    except requests.exceptions.ConnectionError:
        print("连接失败，请检查服务是否运行")
        return

    print("状态码：", response.status_code)

    result = response.json()

    if result["success"]:
        print(result["data"]["answer"])
    else:
        print(result["message"])


ask_agent()