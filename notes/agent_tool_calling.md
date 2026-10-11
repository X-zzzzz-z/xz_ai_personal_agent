# Agent 工具调用流程

- 学习日期：2026-10-05
- 关键词：Tool Calling、Schema、Registry、tool_call_id

## Schema 的作用

Agent将用户消息和工具Schema发送给LLM。

Schema描述了工具名称、功能说明和参数规则，使LLM可以根据用户的问题判断是否需要调用工具、调用哪个工具以及应该传入哪些参数。

## Registry 的作用

Registry是工具注册表，保存工具名称与Python函数之间的对应关系。

Agent可以根据LLM返回的工具名称，从Registry中找到并执行对应的Python函数。

## 完整执行流程

Agent收到用户消息后，将用户消息和工具Schema发送给LLM。

LLM判断是否需要调用工具。如果需要，LLM返回工具名称、工具参数和tool_call_id等信息。

Agent根据工具名称在Registry中找到对应的Python函数，并使用LLM生成的参数执行函数。

工具执行完成后，Agent把执行结果作为tool消息加入messages，并使用tool_call_id将工具结果与之前的工具调用对应起来。

然后Agent再次调用LLM。LLM结合用户最初的问题、对话上下文和工具执行结果，生成最终的自然语言回答。

## tool_call_id 的作用

tool_call_id用于标识一次具体的工具调用，并将工具执行结果与对应的工具调用关联起来。

当LLM一次发起多个工具调用时，tool_call_id可以避免不同工具的执行结果发生混淆。

## 还没有掌握

目前已经理解Agent工具调用的完整流程，但还不能完全脱离提示独立写出Schema生成、Registry注册和工具调用循环，需要继续通过项目练习。