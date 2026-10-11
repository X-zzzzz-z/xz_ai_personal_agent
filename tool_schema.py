#inspect： 检查/查看   检查参数结构：有哪些参数，参数类型，参数默认值，必填参数
import inspect

#python类型转化为json schema类型
#keyword: str    ->    "keyword":{"type": "string"}
TYPE_MAP = {                    
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean"
}

def generate_schema(func):                                   #generate: 生成
    """根据Python函数自动生成工具Schema"""
    signature = inspect.signature(func)                      #signature: 保存函数签名

    properties = {}                                          #保存每个参数的类型等信息
    required = []                                            #保存所有必填参数的名称

    for name,param in signature.parameters.items():         #signature.parameters： 获得函数的所有参数    items: 同时取出参数名称和参数信息
        python_type = param.annotation                       #读取参数的类型注解
        schema_type = TYPE_MAP.get(python_type,"string")

        properties[name] = {
            "type": schema_type
        }

        if param.default is inspect.Parameter.empty:         #检查参数有没有默认值
            required.append(name)                            #没有默认值说明调用时必须提供添加参数信息

    return {
        "type": "function",
        "function": {
            "name": func.__name__,                           #func.__name__: 获取函数名称  例如： "search_notes"
            "description": (func.__doc__ or "").strip(),     #description: 工具说明     func.__doc__：获取说明文字      strip(): 清除两端空白
            "parameters": {                                  #perameters: 参数规则
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }


def tool(func):                                              #tool接收一个函数对象
    """为工具函数自动生成并绑定Schema"""
    func.schema = generate_schema(func)                      #生成Schema，保存到函数的schema属性   
    return func