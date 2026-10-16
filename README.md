# XZ AI Personal Learning Agent

## 项目简介

XZ AI Personal Learning Agent 是一个面向学生和自学者的个人学习管理 Agent，用于记录学习内容、查询历史记录和检索 Markdown 学习笔记。

项目已接入大语言模型与 Tool Calling。用户通过自然语言提出需求，由模型选择工具，程序检查并执行工具，再将结果反馈给模型生成回答。

笔记检索采用基于文本向量的语义搜索，检索相关笔记片段，为模型回答提供上下文。项目支持命令行问答和 FastAPI HTTP 接口，可通过接口文档或 Python 客户端调用。

## 当前功能

- 通过自然语言添加学习记录、查询记录和检索笔记。
- 按关键词或日期直接查询学习记录。
- 使用MySQL保存学习记录，支持参数化插入和条件查询。
- 语义检索 Markdown 学习笔记。
- 检查工具参数的 JSON 格式和调用结构。
- 在学习工具中校验参数，处理数据库异常，并在写入失败时回滚事务。
- 使用统一的结果字典返回工具执行结果。
- 每次问答最多进行三轮模型调用，拦截重复搜索。
- 通过 HTTP 提供健康检查、记录查询、记录添加和自然语言问答接口。
- 校验 HTTP 请求数据，拒绝空问题。
- 使用 Python 客户端发送请求，处理连接失败和超时。

## 技术与实现

| 技术 | 用途 |
|---|---|
| Python | 工具开发、文件处理和 Agent 流程控制 |
| LLM API | 通过 OpenAI 兼容接口调用大语言模型 |
| Tool Calling | 由模型提出工具调用请求，程序执行对应函数 |
| Tool Schema | 描述工具名称、用途和参数结构 |
| Tool Registry | 保存工具名称与 Python 函数的对应关系 |
| Sentence Transformers | 文本编码与相似度计算 |
| RAG | 将检索到的笔记片段反馈给模型，辅助生成回答 |
| FastAPI、Pydantic | HTTP 路由、请求解析和数据校验 |
| Uvicorn | 运行 FastAPI 服务 |
| Requests | 在 Python 客户端中发送 HTTP 请求 |
| MySQL、PyMySQL | 保存学习记录，通过 Python 执行 SQL |
| Markdown | 保存学习笔记 |
| JSON | 传递工具参数、工具结果和 HTTP 请求与响应数据 |

## 项目结构

| 路径 | 作用 |
|---|---|
| agent.py | 提供 run_agent()，控制模型调用、工具执行和结果反馈；支持命令行问答 |
| api.py | 创建 FastAPI 应用，定义请求模型和 HTTP 接口 |
| api_client.py | HTTP 调用示例，发送问答请求并显示回答 |
| llm.py | 配置模型客户端，封装模型请求 |
| learning_tools.py | 实现记录添加、记录查询和笔记搜索工具 |
| rag.py | 实现文本编码、相似度计算和语义检索 |
| tool_registry.py | 注册工具、按名称查找函数、获取工具 Schema |
| tool_schema.py | 为工具函数生成 Schema |
| requirements.txt | 项目依赖清单 |
| .env.example | 环境变量配置示例 |
| data/learning_records.json | 旧版学习记录文件，历史数据尚未自动迁移到 MySQL |
| notes/ | 保存 Markdown 学习笔记 |
| README.md | 项目说明 |
| database.py | 读取数据库配置，提供 get_connection() 连接函数 |
| init.sql | 初始化 MySQL 数据库、学习记录表和日期索引 |

## 核心流程

1. 命令行接收问题，或 FastAPI 解析并校验请求体。
2. 调用 run_agent()，构建系统消息和用户消息。
3. 将消息列表和工具 Schema 发送给模型。
4. 保存模型返回的 assistant 消息。
5. 如果模型请求工具，解析工具名称和 JSON 参数。
6. 查找工具函数，检查调用结构，执行工具及其内部参数校验。
7. 将工具结果封装为 tool 消息，通过 tool_call_id 关联对应调用。
8. 将更新后的消息列表再次发送给模型。
9. 模型返回普通回答后，结束本次处理并返回结果。
10. HTTP 调用时，接口将结果作为 JSON 响应返回客户端。

GET /records 和 POST /records 直接调用学习记录工具，不经过模型决策。POST /chat 调用 Agent，处理自然语言问题。

## 工具说明

| 工具 | 功能 |
|---|---|
| add_learning_record() | 添加学习记录并提交保存到 MySQL |
| query_learning_records() | 按关键词或日期查询学习记录 |
| semantic_search_notes() | 语义检索 Markdown 笔记，返回相关片段 |

### 学习记录字段

| 字段 | 含义 |
|---|---|
| date | 学习日期，格式为 YYYY-MM-DD |
| title | 学习标题 |
| content | 学习内容 |
| key_points | 关键知识点 |
| unresolved | 未解决的问题 |

### 工具结果格式

工具使用统一的结果结构：

~~~python
{
    "success": True,
    "message": "执行结果说明",
    "data": ...
}
~~~

success 表示业务是否成功，message 提供结果说明，data 保存返回的数据。工具失败时通常返回 success=False、错误说明和 data=None。

## 运行方法

### 1. 准备环境

当前已运行验证的环境：Windows、Python 3.13.15。下列 Windows 命令统一使用 Python 3.13，安装依赖与运行程序应使用同一个解释器。

在项目根目录执行：

~~~powershell
py -3.13 --version
py -3.13 -m pip install -r requirements.txt
~~~

HTTP 服务与客户端需要 fastapi、uvicorn、requests。若依赖清单尚未包含它们，先安装，并将对应依赖补入 requirements.txt：

~~~powershell
py -3.13 -m pip install fastapi uvicorn requests
~~~

使用 VS Code 时，通过 Python: Select Interpreter 选择同一个项目环境。

首次运行可能需要下载文本向量模型：

sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

模型调用需要网络连接和有效的 API Key。

### 2. 配置 API Key 和数据库密码

在项目根目录创建 `.env` 文件，填写自己的配置：

```env
DEEPSEEK_API_KEY=your_api_key
MYSQL_PASSWORD=your_mysql_password
```

- `DEEPSEEK_API_KEY`：大模型 API 密钥。
- `MYSQL_PASSWORD`：本机 MySQL 的 root 用户密码。

上面的值是占位文字，需要替换为自己的真实配置。
`.env` 已加入 Git 忽略规则，真实密钥和密码应保留在本机。

模型名称和 API 地址在 `llm.py` 中配置。
数据库连接在 `database.py` 中配置，目前连接本机
`127.0.0.1:3306`，使用 root 用户和 `xz_agent` 数据库。

### 3. 初始化数据库和准备笔记

需要先安装 MySQL 并启动数据库服务。

在项目根目录的 PowerShell 中连接 MySQL：

```powershell
mysql -u root -p
```

按提示输入数据库密码。进入 `mysql>` 后执行：

```sql
SOURCE init.sql;
```

脚本会在数据库和表不存在时创建它们，并建立日期索引。
它只创建结构，不包含学习记录；已有表不会被清空，
也不会自动更新已有表的结构。

完成后退出 MySQL：

```sql
exit;
```

当前学习记录的添加和查询使用 MySQL。
旧的 `data/learning_records.json` 不再作为这两个工具的数据源，
其中的历史记录尚未自动迁移到数据库。

Markdown 学习笔记仍保存在 `notes/` 文件夹，
由笔记搜索工具读取并进行语义检索。

### 4. 命令行问答

~~~powershell
py -3.13 agent.py
~~~

根据终端提示输入问题。当前命令行程序每次启动处理一个用户问题。

### 5. 启动 HTTP 服务

~~~powershell
py -3.13 -m uvicorn api:app --reload
~~~

等待终端出现 Application startup complete，并保持服务运行。

接口文档地址：

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

--reload 用于开发时自动重载。127.0.0.1 是本机地址，当前启动方式供本机访问。

### 6. 运行 Python 客户端

保持服务运行，在另一个终端执行：

~~~powershell
py -3.13 api_client.py
~~~

当前客户端向 POST /chat 发送示例问题，解析 JSON 响应，并根据 success 显示回答或失败提示。客户端处理连接错误和请求超时。

## HTTP 接口

| 方法 | 路径 | 用途 | 输入 |
|---|---|---|---|
| GET | /health | 检查服务是否能响应 | 无 |
| GET | /records | 查询学习记录 | URL 查询参数 keyword、date |
| POST | /records | 添加学习记录 | JSON 请求体中的五个记录字段 |
| POST | /chat | 自然语言问答 | JSON 请求体中的 question |

### 健康检查

[http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

响应：

~~~json
{"status": "ok"}
~~~

### 查询记录

示例地址：

[http://127.0.0.1:8000/records?keyword=FastAPI&date=2026-10-12](http://127.0.0.1:8000/records?keyword=FastAPI&date=2026-10-12)

keyword、date 均为可选字符串，但至少提供一个有效查询条件。同时提供时，记录必须同时满足两项条件。查询成功时，data 为记录列表；没有匹配记录时为 []。

### 添加记录

向 POST /records 发送 JSON 请求体：

~~~json
{
    "date": "2026-10-13",
    "title": "学习HTTP客户端",
    "content": "使用Python调用FastAPI接口",
    "key_points": "查询参数、JSON请求体、响应解析",
    "unresolved": "继续完善接口错误处理"
}
~~~

五个字段都需要提供字符串，具体值由学习记录工具进一步校验。此请求成功时会实际新增一条记录。

### 自然语言问答

向 POST /chat 发送：

~~~json
{
    "question": "查询我关于FastAPI的学习记录"
}
~~~

成功响应结构：

~~~json
{
    "success": true,
    "message": "问答完成",
    "data": {
        "answer": "模型生成的回答"
    }
}
~~~

问题为空或只包含空白字符时，返回 HTTP 400：

~~~json
{
    "success": false,
    "message": "问题不能为空",
    "data": null
}
~~~

缺少必填 question 字段或请求数据不满足请求模型时，FastAPI 默认返回 HTTP 422，正文使用 detail 错误结构。

### 状态码与业务结果

HTTP 状态码与响应体中的 success 是两个不同的信息，应分别检查。

- 正常返回的业务字典，当前默认使用 HTTP 200。
- POST /chat 的空问题分支明确返回 HTTP 400。
- 请求模型校验失败，默认返回 HTTP 422。
- 访问未登记的路径，通常返回 HTTP 404。
- 已捕获的 Agent 失败目前仍返回业务字典，可能同时出现 HTTP 200 和 success=False。

装饰器中的 responses 用于接口文档说明；实际状态码由运行时返回的响应决定。

## 使用示例

### 搜索学习笔记

~~~text
请搜索我的学习笔记，解释FileNotFoundError，并说明笔记中提到它会在什么情况下出现。
~~~

### 添加学习记录

~~~text
请添加一条学习记录：
日期为2026-10-11；
标题为“联调测试-Agent消息链”；
学习内容为“学习了模型请求工具、执行工具、反馈结果的完整流程”；
关键点为“先保存assistant消息，再保存带tool_call_id的tool消息”；
未解决问题为“待验证记录查询功能”。
~~~

### 查询学习记录

~~~text
请查询2026-10-11的学习记录，找到标题为“联调测试-Agent消息链”的记录，展示学习内容、关键点和未解决问题。
~~~

## 已完成的手动联调验证

以下为接入 MySQL 前的手动测试结果，其中学习记录使用 JSON 文件存储。
这些结果不代表 MySQL 版本的 HTTP 接口已经完成回归验证。
| 场景 | 已观察到的结果 |
|---|---|
| 搜索已有笔记 | 返回相关片段，模型生成回答并标注笔记来源 |
| 搜索无相关内容 | 当前样例提示未找到足够相关内容，没有补写该主题的解释 |
| 添加学习记录 | JSON 文件实际新增记录，五个字段与输入一致 |
| 重启后查询记录 | 成功读回已保存记录，回答内容与记录一致 |
| GET /health | 返回 HTTP 200 和 status=ok |
| GET /records | 按 FastAPI 关键词查到已保存记录 |
| POST /records | 通过接口成功保存学习记录 |
| POST /chat 正常问题 | Python 客户端收到 HTTP 200、success=True 和最终回答 |
| POST /chat 空白问题 | 修改后返回 HTTP 400 和“问题不能为空” |
| POST /chat 缺少 question | 返回 HTTP 422，提示字段缺失 |
| 服务停止时运行客户端 | 捕获连接错误，结束函数后继续执行函数外代码 |
| /chat 接口文档 | 显示中文标题配置，并已确认新增的 HTTP 400 响应说明 |

以上是已有手动测试样例的结果。超时捕获分支已编写，尚未通过受控超时场景验证；尚未建立完整的自动化测试和检索质量评估。

### MySQL 接入后的手动验证

| 场景 | 已观察到的结果 |
|---|---|
| 直接调用添加工具 | 成功写入 MySQL，返回记录编号，并通过 SQL 查询确认 |
| 仅按日期查询 | 返回指定日期的学习记录 |
| 仅按关键词查询 | 返回包含关键词的记录，支持去除关键词两边空格和忽略大小写 |
| 同时提供日期和关键词 | 只返回同时满足两项条件的记录 |
| 查询条件没有匹配记录 | 返回 success=True、data=[] |
| Agent 自然语言添加后重新启动查询 | 成功读回“MySQL Agent闭环验证”记录，编号为 10 |
| GET /records | 通过 HTTP 查询到 MySQL 中编号为 10 的记录 |
| POST /records | 成功添加记录，返回编号 11 |
| POST /chat | 通过自然语言查回编号 11，内容与添加结果一致 |

## 当前限制

- 命令行每次启动处理一个问题；HTTP 请求之间尚未保存多轮对话上下文。
- 单次问答最多进行三轮模型调用，第三轮不再提供工具说明。
- 笔记搜索和记录查询各最多尝试一次，即使调用失败也会记录为已使用。
- 无相关笔记时的回答行为受系统提示词约束，尚未经过大规模验证。
- 历史 JSON 学习记录尚未迁移到 MySQL。
- 尚未提供修改、删除学习记录的 Agent 工具。
- MySQL 接入后的 HTTP 接口尚需回归验证。
- 检索效果依赖笔记内容、分块方式和相关性判断，需要更多样例验证。
- 各类业务失败的 HTTP 状态码，以及默认请求校验错误与业务错误的响应格式，尚未统一。
- 当前 Python 客户端面向示例接口响应，尚未完整处理非 JSON 正文等异常响应。
- 尚未提供网页前端、身份认证及对外部署。
- 学习周报、月报和长期学习建议尚未实现。

## 后续计划

- 同步依赖清单，完善项目运行说明。
- 统一接口错误处理和响应文档。
- 增加异常场景测试与工具调用日志。
- 使用更多问题评估检索效果和答案是否符合笔记。
- 优化笔记向量计算与缓存。
- 拆分 Agent 循环中的职责，提高可读性。
- 增加连续对话和学习周报功能。

## 当前阶段

已完成学习记录工具、语义检索、Agent 工具调用和 FastAPI 接口的集成。已使用接口文档和 Python 客户端验证查询、问答、请求校验及连接失败等场景。

学习记录的添加和查询已接入 MySQL，并完成工具直接调用及 Agent
自然语言添加、重新启动后查询的手动验证。Markdown 笔记仍通过文件读取和语义检索使用。

当前重点是完成代码审查与Git提交，再进入Linux部署学习

