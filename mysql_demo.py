"""
connection.cursor()	基于连接创建游标
sql = ""'...'""	保存 SQL 字符串，此时还没有执行查询
cursor.execute(sql)	将 SQL 发送给 MySQL 执行
cursor.fetchall()	取出本次查询的全部剩余结果
print(record)	打印每条记录
GROUP BY 按指定字段分组
HAVING：筛选分组统计后的结果。
INNER JOIN users：与用户表进行内连接。
参数	作用
host="127.0.0.1"	连接你自己电脑上的 MySQL
port=3306	连接 MySQL 使用的端口
user="root"	使用的 MySQL 账号
password=...	从环境变量取得密码
database="xz_agent"	选择要操作的数据库
charset="utf8mb4"	设置连接使用的字符编码
cursorclass=...DictCursor	让查询出的每一行以字典形式表示
"""

import os
import json

import pymysql
from dotenv import load_dotenv


env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)


def get_connection():
    return pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password=os.getenv("MYSQL_PASSWORD"),
        database="xz_agent",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )


def query_records_by_date(record_date):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT id, record_date, title
            FROM learning_records
            WHERE record_date = %s
            ORDER BY id DESC
            """

            cursor.execute(sql, (record_date,))
            records = cursor.fetchall()

        for record in records:
            record["record_date"] = record["record_date"].isoformat()

        return records

    finally:
        connection.close()

def add_record(record_date, title, content):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO learning_records (
                record_date, title, content
            )
            VALUES (%s, %s, %s)
            """

            cursor.execute(sql, (record_date, title, content))
            record_id = cursor.lastrowid

        connection.commit()         #筛选条件保存
        return record_id

    except pymysql.MySQLError:
        connection.rollback()
        raise

    finally:
        connection.close()

records = query_records_by_date("2026-10-15")

json_text = json.dumps(
    records,
    ensure_ascii=False,
    indent=2
)

print(json_text)