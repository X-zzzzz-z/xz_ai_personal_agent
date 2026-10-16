-- 创建名为 xz_agent 的数据库
-- IF NOT EXISTS：数据库不存在时才创建，已存在就跳过
-- utf8mb4：支持保存中文、表情等字符
CREATE DATABASE IF NOT EXISTS xz_agent
    CHARACTER SET utf8mb4;

-- 选择数据库，后面的建表操作在这个数据库中进行
USE xz_agent;

-- 创建学习记录表，已存在就跳过，不会清空已有记录
CREATE TABLE IF NOT EXISTS learning_records (

    -- 记录编号：整数、主键，新增记录时自动生成
    id INT PRIMARY KEY AUTO_INCREMENT,

    -- 学习日期：日期类型，不能为 NULL
    record_date DATE NOT NULL,

    -- 学习标题：最多 200 个字符，不能为 NULL
    title VARCHAR(200) NOT NULL,

    -- 学习内容：较长的文本，不能为 NULL
    content TEXT NOT NULL,

    -- 学习重点：较长的文本，允许为 NULL
    key_points TEXT,

    -- 未掌握内容：较长的文本，允许为 NULL
    unresolved TEXT,

    -- 为学习日期建立索引，帮助按日期查找记录
    -- idx_record_date 是我们给索引起的名字
    INDEX idx_record_date (record_date)

-- InnoDB：使用支持事务的存储引擎，可以提交或回滚事务
-- DEFAULT CHARSET：设置表的默认字符集
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;