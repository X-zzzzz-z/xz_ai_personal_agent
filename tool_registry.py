class ToolRegistry:
    """管理可以被Agent调用的工具"""


    #创建工具字典
    def __init__(self):
        self.tools = {}             #创建工具字典，保存{"工具名称"：工具对应的函数对象}

    #创建工具注册表
    def register(self,func):
        """注册一个工具函数"""
        if not hasattr(func, "schema"):             #hansattr是has attribute： 是否拥有某个属性
            raise ValueError(                       #主动抛出错误，防止不完整工具加入Rigistry
                f"工具{func.__name__}没有Schema，请先使用@tool装饰器"   
            )
        tool_name = func.__name__
        self.tools[tool_name] = func


    #添加两个查询方法Python函数
    #1.根据工具名称获取
    def get_tool(self,tool_name):
        """根据工具名称获取Python函数"""
        if tool_name not in self.tools:
            raise ValueError(f"工具不存在:{tool_name}")
        
        return self.tools[tool_name]


    #2.获取所有工具的Schema
    def get_schema(self):
        """获取所有工具的Schema"""
        return [
            func.schema                             #取出每个函数的Schema
            for func in self.tools.values()         #只取字典中的所有函数
        ]


