from agent import execute_tool
from tool_registry import ToolRegistry
from learning_tools import add_learning_record

registry = ToolRegistry()
registry.register(add_learning_record)

cases = [
    ("JSON格式错误", "add_learning_record", "{"),
    ("JSON不是对象", "add_learning_record", "[]"),
    ("工具不存在", "unknown_tool", "{}"),
]

for label, tool_name, arguments in cases:
    result = execute_tool(registry, tool_name, arguments)
    print(label, result)