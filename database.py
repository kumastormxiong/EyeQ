import sqlite3
import os
import hashlib

def get_db_path():
    """
    获取数据库文件的绝对路径。
    如果data目录不存在，则会创建它。
    
    :return: 数据库文件的完整路径 (str)
    """
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return os.path.join(data_dir, 'conversations.db')

def _add_column_if_not_exists(cursor, table_name, column_info):
    """
    一个辅助函数，用于检查表中是否存在某个列，如果不存在则添加。
    :param cursor: 数据库游标
    :param table_name: 表名
    :param column_info: 列的完整定义 (例如 'user_id INTEGER')
    """
    column_name = column_info.split()[0]
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    if column_name not in columns:
        print(f"Adding column {column_name} to table {table_name}...")
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_info}")

def hash_password(password):
    """
    对明文密码进行SHA256哈希。
    :param password: 明文密码 (str)
    :return: 哈希后的密码 (str)
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db():
    """
    初始化数据库。
    users表增加password字段（如无则自动添加），并为老用户补全密码。
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # 用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number TEXT UNIQUE NOT NULL
    )''')
    # 截图表
    c.execute('''CREATE TABLE IF NOT EXISTS screenshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT,
        timestamp TEXT
    )''')
    # 对话表
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT,
        screenshot_id INTEGER,
        timestamp TEXT
    )''')
    # 迁移：为旧表添加user_id
    _add_column_if_not_exists(c, 'screenshots', 'user_id INTEGER')
    _add_column_if_not_exists(c, 'conversations', 'user_id INTEGER')
    # 迁移：为users表添加password字段
    _add_column_if_not_exists(c, 'users', 'password TEXT')
    # 为老用户补全password字段（如有空值）
    c.execute("UPDATE users SET password = ? WHERE password IS NULL OR password = ''", (hash_password(''),))
    conn.commit()
    conn.close()

def get_or_create_user(phone_number, password=None):
    """
    根据手机号获取或注册用户。
    注册时需提供密码。
    :param phone_number: 手机号 (str)
    :param password: 明文密码 (str)，注册时必填
    :return: 用户ID (int) 或 None（密码错误）
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT id, password FROM users WHERE phone_number = ?', (phone_number,))
    user = c.fetchone()
    if user:
        # 已注册，校验密码
        if password is not None and user[1] == hash_password(password):
            user_id = user[0]
        elif password is None:
            user_id = user[0]
        else:
            user_id = None
    else:
        # 新用户注册
        if password:
            c.execute('INSERT INTO users (phone_number, password) VALUES (?, ?)', (phone_number, hash_password(password)))
            user_id = c.lastrowid
        else:
            user_id = None
    conn.commit()
    conn.close()
    return user_id

# 强制重置指定手机号的密码为123321123
try:
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('UPDATE users SET password=? WHERE phone_number=?', (hash_password('123321123'), '15928179492'))
    conn.commit()
    conn.close()
except Exception as e:
    print('重置15928179492密码失败:', e)

def insert_screenshot(user_id, path, timestamp):
    """
    向数据库中插入一条新的截图记录。
    
    :param user_id: 进行截图操作的用户ID (int)
    :param path: 截图文件的保存路径 (str)
    :param timestamp: 截图发生时的时间戳 (str)
    :return: 新插入的截图记录的ID (int)
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT INTO screenshots (user_id, path, timestamp) VALUES (?, ?, ?)', (user_id, path, timestamp))
    screenshot_id = c.lastrowid
    conn.commit()
    conn.close()
    return screenshot_id

def insert_conversation(user_id, question, answer, screenshot_id, timestamp):
    """
    向数据库中插入一条新的对话记录。
    
    :param user_id: 进行对话的用户ID (int)
    :param question: 用户提出的问题 (str)
    :param answer: AI返回的回答 (str)
    :param screenshot_id: 关联的截图ID，可以为None (int)
    :param timestamp: 对话发生时的时间戳 (str)
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT INTO conversations (user_id, question, answer, screenshot_id, timestamp) VALUES (?, ?, ?, ?, ?)',
              (user_id, question, answer, screenshot_id, timestamp))
    conn.commit()
    conn.close() 

def load_conversations(user_id):
    """
    根据用户ID加载其所有对话历史。
    
    :param user_id: 要加载历史记录的用户ID (int)
    :return: 一个包含(question, answer)元组的列表 (list)
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT question, answer
        FROM conversations
        WHERE user_id = ?
        ORDER BY timestamp ASC
    ''', (user_id,))
    history = c.fetchall()
    conn.close()
    return history 

def check_user_password(phone_number, password):
    """
    检查手机号和密码是否匹配。
    :return: 用户ID (int) 或 None
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT id, password FROM users WHERE phone_number = ?', (phone_number,))
    user = c.fetchone()
    conn.close()
    if user and user[1] == hash_password(password):
        return user[0]
    return None 

def get_user_stats(user_id):
    """
    获取用户的统计信息，包括用户名（手机号）和总提问数。
    :param user_id: 用户ID
    :return: (phone_number, total_questions) 元组，如果找不到则返回 None
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # 获取用户名
    c.execute("SELECT phone_number FROM users WHERE id = ?", (user_id,))
    user_result = c.fetchone()
    if not user_result:
        conn.close()
        return None
    phone_number = user_result[0]
    # 获取总提问数
    c.execute("SELECT COUNT(id) FROM conversations WHERE user_id = ?", (user_id,))
    questions_result = c.fetchone()
    total_questions = questions_result[0] if questions_result else 0
    conn.close()
    return phone_number, total_questions 