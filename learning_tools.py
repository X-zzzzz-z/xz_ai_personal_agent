import json
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   
DATA_FILE = os.path.join(BASE_DIR, "data", "learning_records.json")
NOTES_DIR = os.path.join(BASE_DIR, "notes")
from datetime import datetime
from tool_schema import tool
from rag import semantic_search


#辅助函数，用于读取
def _load_learning_records():
    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    )as file:
        records = json.load(file)
    if not isinstance(records,list):
        raise ValueError("学习记录最外层必须是列表")
    return records


#第一个工具：添加学习记录
@tool
def add_learning_record(
        date: str,
        title: str,
        content: str,
        key_points: str,
        unresolved: str
):
    """添加学习记录，包括日期、标题、内容、学习重点和未掌握内容"""
    required_fields = {
        "date":date,
        "title":title,
        "content":content,
        "key_points":key_points,
        "unresolved":unresolved
    }

    #执行前错误处理
    errors = []

    for field_name,value in required_fields.items():            #字段格式校验
        if not isinstance(value,str) or not value.strip():
            errors.append(f"{field_name}必须是非空字符串")

    if isinstance(date,str) and date.strip():                   #日期格式校验
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            errors.append("date必须是 YYYY-MM-DD格式的有效日期")
    if errors:
        return {
            "success": False,
            "message": "参数错误："+";".join(errors),
            "data": None
        }

    try:
        records = _load_learning_records()
    except FileNotFoundError:                   #文件不存在，records=[]，自动创建文件
        records = []
    except json.JSONDecodeError:                #JSON内容损害，立即返回错误，防止覆盖内容
        return {
            "success": False,
            "message": f"数据文件错误：{DATA_FILE} 不是有效的JSON,已停止写入",
            "data": None
        }
    except ValueError as error:
        return {
            "success": False,
            "message": f"数据文件格式错误：{error}",
            "data": None
        }

    record = {                                  #保存到JSON里字段名称：函数收到的参数值
        "date":date,
        "title":title,
        "content":content,
        "key_points":key_points,
        "unresolved":unresolved
    }
    records.append(record)

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    )as file:
        json.dump(
            records,
            file,
            ensure_ascii=False,
            indent=4
        )
    return {
        "success": True,
        "message": f"学习记录保存成功: {title}",
        "data": record
    }


#第二个工具：查询学习记录           keyword： 关键词   matches： 匹配结果
@tool
def query_learning_records(
    keyword: str = "",
    date: str = ""
):
    """按关键词或日期查询学习记录，至少提供一个查询条件"""
    if not isinstance(keyword,str) or not isinstance(date,str):
        return {
            "success": False,
            "message": "参数错误：keyword和date必须是字符串",
            "data": None
        }
    if not keyword.strip() and not date.strip():
        return {
            "success": False,
            "message": "参数错误：请至少提供关键词或日期",
            "data": None
        }

    date_value = date.strip()

    if date_value:
        try:
            datetime.strptime(date_value,"%Y-%m-%d")
        except ValueError:
            return {
                "success": False,
                "message": "参数错误：date必须是有效的 YYYY-MM-DD格式",
                "data": None
            }
        
    try:
        records = _load_learning_records()
    except FileNotFoundError:
        return {
            "success": False,
            "message": "查询失败：学习记录文件不存在",
            "data": None
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "message": "查询失败：学习记录不是有效的JSON",
            "data": None
        }
    except ValueError as error:
        return {
            "success": False,
            "message": f"查询失败：{error}",
            "data": None
        }

    matches = []                                    #matches  匹配结果  lower   转换为小写
    keyword_lower = keyword.strip().lower()         #keyword_lower   将搜索关键字转换小写

    for record in records:
        search_text = " ".join([                    #search_text  搜索的文本  join  拼接
            record.get("title",""),
            record.get("content",""),
            record.get("key_points",""),
            record.get("unresolved","")
        ]).lower()

        keyword_match = not keyword_lower or keyword_lower in search_text
        date_match = not date_value or record.get("date","") == date_value
        if keyword_match and date_match:
            matches.append(record)

    if not matches:
        return {
            "success": True,
            "message": "没有找到匹配的学习记录",
            "data": []
        }
    return {
        "success": True,
        "message": f"找到{len(matches)}条学习记录",
        "data": matches
    }


#辅助函数：找出小节标题
def split_markdown_sections(content: str):              #split:切分；section:小节.
    sections = []

    for line in content.splitlines():                   #line：一行
        if line.startswith("## "):                      #以......开头
            heading = line[3:].strip()
            sections.append({
                "heading": heading,
                "content": ""
            })
        else:
            if sections:
                sections[-1]["content"] += line + "\n"
    return sections


#辅助函数：读取全部笔记片段
#load:加载、读取  note：笔记  chunk：文本片段  _...:表示这是内部使用的辅助函数
#path：路径  isdir：is directory  是不是目录  raise：抛出异常、主动触发错误
def _load_note_chunks():
    if not os.path.isdir(NOTES_DIR):
        raise FileNotFoundError("笔记目录不存在")
    chunks = []
    file_names = os.listdir(NOTES_DIR)

#endswith:结尾  join：拼接
    for file_name in file_names:
        if not file_name.lower().endswith(".md"):
            continue

        file_path = os.path.join(NOTES_DIR,file_name)
        with open(
            file_path,
            "r",
            encoding="utf-8"
        )as file:
            content = file.read()

#section:一个小节  section_content:当前小节的正文内容  split：切分  heading:标题
        sections = split_markdown_sections(content)
        for section in sections:
            section_content = section["content"].strip()

            if not section_content:
                continue

            chunks.append({
                "file_name":file_name,
                "heading":section["heading"],
                "content":section_content
            })
    return chunks


#Markdown笔记切成chunks，拼成texts
#读取笔记片段，调用 rag.py 排序，再整理返回结果。
@tool
def semantic_search_notes(query: str):
    """根据用户问题，对Markdown笔记进行语义搜索"""

#异常处理
    if not isinstance(query,str) or not query.strip():
        return{
            "success": False,
            "message": "参数错误：query必须是非空字符串",
            "data": None
        }
    try:
        chunks = _load_note_chunks()        #尝试从笔记目录读取片段
    except FileNotFoundError:
        return {
            "success": False,
            "message": "搜索失败，笔记目录不存在",
            "data": None
        }
    except(OSError,UnicodeDecodeError) as error:            #读取文件发生系统错误或文本解码失败
        return{
            "success": False,
            "message": f"搜索失败：无法读取笔记：{error}",
            "data": None
        }
    
    if not chunks:                 #检查是否一个可搜索片段都没有。这里目录可能存在，只是没有符合条件的笔记小节
        return {
            "success": True,        #读取过程没有出错，只是结果为空，用空列表表示没有结果
            "message": "没有可搜索的笔记片段",
            "data": []
        }

    texts = []

    for chunk in chunks:
        text = chunk["heading"] + "\n" + chunk["content"]
        texts.append(text)

#actual: 实际的  actual_top_k:实际可以取出的数量
    actual_top_k = min(3,len(texts))

#top_k：取相似度最高的多少条  
    search_results = semantic_search(
        query=query.strip(),
        texts=texts,
        top_k=actual_top_k
    )

    minimum_score = 0.4
    matches = []                        #符合条件的结果

    for result in search_results:
        if result["score"] < minimum_score:
            continue

        chunk = chunks[result["index"]]    #在rag.py里result中找到"index"的值例如1，chunks[1]是选取第二个片段。

#minimum:最低的   matches:符合条件的匹配结果
        matches.append({
            "file_name": chunk["file_name"],
            "heading": chunk["heading"],
            "content": chunk["content"],
            "score": result["score"]
        })

#统一返回结果：
    if not matches:
        return{
            "success": True,
            "message": "没有找到足够相关的笔记",
            "data": []
        }

    return {
        "success": True,
        "message": f"找到{len(matches)}个相关笔记片段",
        "data": matches
    }



#第三个工具：搜索笔记              @tool： 装饰器
@tool                           
def search_notes(keyword: str):
    """根据关键词搜索Markdown笔记"""
    if not isinstance(keyword, str):
        return {
            "success": False,
            "message": "参数错误：keyword必须是字符串",
            "data": None
        }
    
    keyword_lower = keyword.strip().lower()                     #提示词标准化
    if not keyword_lower:
        return {
            "success": False,
            "message": "参数错误：keyword不能为空",
            "data": None
        }
    
    if not os.path.isdir(NOTES_DIR):
        return {
            "success": False,
            "message": "搜索失败：笔记目录不存在",
            "data": None
        }
    
    file_names = os.listdir(NOTES_DIR)                          #listdir  列出目录内容

    matches = []                                                #matches  匹配结果
    for file_name in file_names:
        if not file_name.lower().endswith(".md"):
            continue

        file_path = os.path.join(NOTES_DIR, file_name)          #file_path  文件路径
        try:
            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:
                content = file.read()
        except (OSError,UnicodeDecodeError) as error:
            return {
                "success": False,
                "message": f"搜索失败：无法读取笔记{file_name}:{error}" ,
                "data": None
            }  #OSError：操作系统相关错误，包括文件消失、没有权限等； #UnicodeDecodeError：文件内容不能按指定编码解码； #as error：把捕获到的异常保存到变量 error

        sections = split_markdown_sections(content)
        file_name_match = keyword_lower in file_name.lower()
        for section in sections:
            heading_match = keyword_lower in section["heading"].lower()
            content_match = keyword_lower in section["content"].lower()
            if file_name_match or heading_match or content_match:
                matches.append({
                    "file_name": file_name,
                    "heading": section["heading"],
                    "content": section["content"].strip()
                })

    if not matches:
        return {
            "success": False,
            "message": "没有找到匹配的笔记",
            "data": None
        }
    return {
        "success": True,
        "message": f"找到{len(matches)}个匹配的笔记片段",
        "data": matches
    }


#测试代码：
if __name__ == "__main__":
    result = semantic_search_notes(
        "搜索JSON文件为什么无法读取"
    )
    print(result)