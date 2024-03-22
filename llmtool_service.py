import uuid
from flask import Flask, request, jsonify
from utilities import logger
from flask_cors import CORS
import sys
from xinference.client import Client
import mysql.connector

#app = Flask(__name__)
mylogger = logger.Logger(name='llmtool', debug=True).logger  
app = Flask(__name__)  
CORS(app)

mysql_db_config = {
    "host": "10.101.9.50",
    "user": 'root',
    "password": 'newpass',
    "database": 'codebase'
}

db_connection = mysql.connector.connect(**mysql_db_config)
db_cursor = db_connection.cursor()
if db_connection.is_connected():
    mylogger.debug("Successfully connect mysql database")

mylogger.debug(mysql_db_config)
def execute_query(query, params=()):
    db_cursor.execute(query, params)
    if query.strip().startswith("SELECT"):
        pass
    else:
        db_connection.commit() 
# 使用字典模拟用户存储，实际项目中应使用数据库
users_db = {
    "admin": {"password": "123456"},
    'zz': {'password': 'zz'},
    'xyz': {'password': 'abc'}
}

# 存储登录成功的用户session数据
sessions = {}

x_addr = 'http://10.101.9.50:9998'
mylogger.debug(f"Start to connect xinference server at {x_addr}")
try:
    client = Client(x_addr)    
    model_uid = client.launch_model(model_name="bge-large-zh-v1.5", model_type="embedding")    
    model = client.get_model(model_uid)
except Exception as e:
    mylogger.error(f"Something goes wrong: {e}")    
    sys.exit(1)

def create_embedding_bge(sentence):
    result = model.create_embedding(sentence)
    embedding = result['data'][0]['embedding']
    # LOG.debug(f"length of embedding {len(embedding)}, {embedding[:5]}")
    return embedding

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    clear_expired_user_keys()  # 清理过期的userKey

    if username in users_db and users_db[username]['password'] == password:
        # 生成一个随机的session key
        session_key = str(uuid.uuid4())
        
        query = "DELETE FROM user_sessions WHERE username = %s"
        execute_query(query, (username,))
        query = "INSERT INTO user_sessions (userKey, username) VALUES (%s, %s)"
        execute_query(query, (session_key, username))
                
        # 返回成功响应，包含session key
        response = jsonify({"status": "success", "key": session_key})
        mylogger.debug(f'User {username} has entered, key is [{session_key}]')

        return response, 200
    else:
        mylogger.error(f'User {username} login failed')
        return jsonify({"status": "fail", "message": "用户名或密码错误"}), 401

@app.route('/test', methods=['POST'])
def test():
    username = request.json.get('username')
    password = request.json.get('password')
    userKey = request.json.get('userKey')

    mylogger.debug(f"test ==> {userKey}")
    query = 'SELECT username, last_refresh FROM user_sessions WHERE userKey = %s'
    execute_query(query, (userKey,))
    res = db_cursor.fetchone()
    if res:
        return jsonify({"status": "success", "content": f'Your username is {res[0]}'}), 200
    else:
        return jsonify({"status": "fail", "message": "请先登录"}), 401
        
# 添加checkLogin服务
@app.route('/checkLogin', methods=['POST'])
def check_login():
    user_key = request.json.get('userKey')
    mylogger.debug(f"checkLogin ==> {user_key}")
    clear_expired_user_keys()
    query = 'SELECT username, last_refresh FROM user_sessions WHERE userKey = %s'
    execute_query(query, (user_key,))
    res = db_cursor.fetchone()
    if res:
        return jsonify({"status": "success", "username": res[0]}), 200
    else:
        return jsonify({"status": "fail", "message": "验证失败"}), 401           
    
def generate_float_list():
    float_list = [round(i * 0.01, 2) for i in range(1, 1025)]
    return float_list

def clear_expired_user_keys():    
    # 删除1小时前更新的userKey
    query = "DELETE FROM user_sessions WHERE last_refresh < (NOW() - INTERVAL 1 HOUR)"
    execute_query(query)

@app.route('/genvec', methods=['POST'])
def get_float_list():
    question = request.json.get('question')
    mylogger.debug(f'Get question: {question}')
    #float_list = generate_float_list()
    float_list = create_embedding_bge(question)
    return jsonify(float_list)

if __name__ == '__main__':
    host = 'localhost'
    app.run(debug=False, host=host, port=5111)

# 在实际应用中，还需实现logout等接口，清除对应session_key的数据，并且考虑session过期等问题