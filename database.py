#数据库连接函数
import os

import pymysql
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE)

#定义创建连接的方法
def get_connection():
    return pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password=os.getenv("MYSQL_PASSWORD"),
        database="xz_agent",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False        #autocommit  不自动提交。添加数据后需要调用commit();失败是回滚
    )