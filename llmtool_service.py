import uuid
from flask import Flask, request, jsonify
from utilities import logger
from flask_cors import CORS
import sys
from xinference.client import Client
from datetime import datetime, timedelta
import schedule

#app = Flask(__name__)
mylogger = logger.Logger(name='llmtool', debug=True).logger  
app = Flask(__name__)  
CORS(app)

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

    if username in users_db and users_db[username]['password'] == password:
        # 生成一个随机的session key
        session_key = str(uuid.uuid4())
        
        # 将username和session_key关联并保存
        sessions[session_key] = {'username': username}
        sessions[session_key]['last_refresh'] = datetime.now()
        
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

    if userKey is not None and sessions[userKey] is not None:
        mylogger.debug(f'Find correct key for user {username}')
        response = jsonify({"status": "success", "content": f'Your username is {sessions[userKey]}'})
        return response, 200
    else:
        mylogger.error(f'Key error')
        return jsonify({"status": "fail", "message": "请先登录"}), 401

# 添加checkLogin服务
@app.route('/checkLogin', methods=['POST'])
def check_login():
    user_key = request.json.get('userKey')
    
    if user_key in sessions:
        # 更新userKey的刷新时间
        sessions[user_key]['last_refresh'] = datetime.now()
        
        # 返回username
        username = sessions[user_key]['username']
        return jsonify({"status": "success", "username": username}), 200
    else:
        return jsonify({"status": "fail", "message": "验证失败"}), 401
    
def generate_float_list():
    float_list = [round(i * 0.01, 2) for i in range(1, 1025)]
    return float_list

# 定时清除过期userKey
def clear_expired_sessions():
    current_time = datetime.now()
    for key, value in sessions.items():
        last_refresh_time = value.get('last_refresh')
        if last_refresh_time and current_time - last_refresh_time > timedelta(hours=1):
            del sessions[key]

@app.route('/genvec', methods=['POST'])
def get_float_list():
    question = request.json.get('question')
    mylogger.debug(f'Get question: {question}')
    #float_list = generate_float_list()
    float_list = create_embedding_bge(question)
    return jsonify(float_list)

if __name__ == '__main__':
    host = 'localhost'
    schedule.every().hour.do(clear_expired_sessions)
    app.run(debug=False, host=host, port=5111)

# 在实际应用中，还需实现logout等接口，清除对应session_key的数据，并且考虑session过期等问题