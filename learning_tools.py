import pymysql
import json
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "learning_records.json")
NOTES_DIR = os.path.join(BASE_DIR, "notes")
from database import get_connection
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
        "date": date,
        "title": title,
        "content": content,
        "key_points": key_points,
        "unresolved": unresolved
    }

    errors = []

    #参数校验
    for field_name, value in required_fields.items():
        #检查输入是否合格
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name}必须是非空字符串")

    if isinstance(date, str) and date.strip():
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            errors.append("date必须是 YYYY-MM-DD格式的有效日期")

    if errors:
        return {
            "success": False,
            "message": "参数错误：" + ";".join(errors),
            "data": None
        }

    #准备成功时返回给Agent的数据。
    record = {
        "date": date,
        "title": title,
        "content": content,
        "key_points": key_points,
        "unresolved": unresolved
    }

    connection = None

    try:
        #建立SQL连接
        connection = get_connection()

        with connection.cursor() as cursor:
            sql = """
            INSERT INTO learning_records (
                record_date,
                title,
                content,
                key_points,
                unresolved
            )
            VALUES (%s, %s, %s, %s, %s)
            """

            #新增记录到数据库
            cursor.execute(
                sql,
                (date, title, content, key_points, unresolved)
            )

            record_id = cursor.lastrowid

        connection.commit()

    except pymysql.MySQLError as error:
        if connection is not None:
            connection.rollback()

        return {
            "success": False,
            "message": f"数据库保存失败：{error}",
            "data": None
        }

    finally:
        if connection is not None:
            connection.close()

    record["id"] = record_id

    return {
        "success": True,
        "message": f"学习记录保存成功：{title}",
        "data": record
    }


#第二个工具：查询学习记录           keyword： 关键词   matches： 匹配结果
@tool
def query_learning_records(
    keyword: str = "",
    date: str = ""
):
    """按关键词或日期查询学习记录，至少提供一个查询条件"""
    #检查参数是不是字符串
    if not isinstance(keyword, str) or not isinstance(date, str):
        return {
            "success": False,
            "message": "参数错误：keyword和date必须是字符串",
            "data": None
        }

    keyword_value = keyword.strip().lower()
    date_value = date.strip()

    #检查是否至少提供了一个查询条件
    if not keyword_value and not date_value:
        return {
            "success": False,
            "message": "参数错误：请至少提供关键词或日期",
            "data": None
        }

    #检查日期格式是不是%Y-%m-%d
    if date_value:
        try:
            datetime.strptime(date_value, "%Y-%m-%d")
        except ValueError:
            return {
                "success": False,
                "message": "参数错误：date必须是有效的 YYYY-MM-DD格式",
                "data": None
            }

    #保存查询条件、参数值
    conditions = []     #条件列表、保存SQL条件片段。
    params = []     #参数列表、保存%s对应的实际值

    if date_value:
        conditions.append("record_date = %s")
        params.append(date_value)

    #有关键词时，增加关键词条件
    #concat_ws('',...)  用空格连接标题、内容、重点、未掌握内容；跳过NULL
    #lower() 把连接后的文本转换为小写
    #locate(关键词，文本)  查找关键词的位置；找不到返回0
    #>0  表示找到了关键词
    if keyword_value:
        conditions.append("""
            LOCATE(
                %s,
                LOWER(CONCAT_WS(
                    ' ', title, content, key_points, unresolved
                ))
            ) > 0
        """)
        params.append(keyword_value)

    sql = """
        SELECT
            id,
            record_date AS date,
            title,
            content,
            key_points,
            unresolved
        FROM learning_records
        WHERE
    """

    sql += " AND ".join(conditions)
    sql += " ORDER BY record_date DESC, id DESC"

    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(sql, tuple(params))      #tuple(params)把参数列表转换为元组
            matches = list(cursor.fetchall())

        for record in matches:
            record["date"] = record["date"].isoformat()

    except pymysql.MySQLError as error:
        return {
            "success": False,
            "message": f"数据库查询失败：{error}",
            "data": None
        }

    finally:
        if connection is not None:
            connection.close()

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