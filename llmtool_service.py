import uuid
from flask import Flask, request, jsonify
from utilities import logger
from flask_cors import CORS
import sys
from xinference.client import Client
import mysql.connector
import json
from utilities.dbtool import DBHandler
import numpy as np
from pydantic import BaseModel
from typing import List
from scipy.interpolate import interp1d
from sklearn.preprocessing import PolynomialFeatures
#from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
#app = Flask(__name__)
mylogger = logger.Logger(name='llmtool', debug=True).logger  
app = Flask(__name__)  
CORS(app)

db_handler = DBHandler('users')
# mysql_db_config = {
#     "host": "10.101.9.50",
#     "user": 'root',
#     "password": 'newpass',
#     "database": 'codebase'
# }

# db_connection = mysql.connector.connect(**mysql_db_config)
# db_cursor = db_connection.cursor()
# if db_connection.is_connected():
#     mylogger.debug("Successfully connect mysql database")

# mylogger.debug(mysql_db_config)
# def execute_query(query, params=()):
#     db_cursor.execute(query, params)
#     if query.strip().startswith("SELECT"):
#         pass
#     else:
#         db_connection.commit() 

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

def create_embedding_bge_np(sentence):
    result = model.create_embedding(sentence)
    embedding = result['data'][0]['embedding']
    # LOG.debug(f"length of embedding {len(embedding)}, {embedding[:5]}")
    return np.array(embedding)

def checkUser(username, password):
    query = "SELECT * FROM user_info WHERE username=%s and mypwd=%s"
    db_handler.execute_query(query,(username, password))
    res = db_handler.fetchone()
    if res:
        return True
    else:
        return False

class EmbeddingRequest(BaseModel):
    input: 'List[str]|str'
    model: str

class EmbeddingResponse(BaseModel):
    data: list
    model: str
    object: str
    usage: dict
# 插值法
def interpolate_vector(vector, target_length):
    original_indices = np.arange(len(vector))
    target_indices = np.linspace(0, len(vector)-1, target_length)
    f = interp1d(original_indices, vector, kind='linear')
    return f(target_indices)

def expand_features(embedding, target_length):
    poly = PolynomialFeatures(degree=2)
    expanded_embedding = poly.fit_transform(embedding.reshape(1, -1))
    expanded_embedding = expanded_embedding.flatten()
    if len(expanded_embedding) > target_length:
        # 如果扩展后的特征超过目标长度，可以通过截断或其他方法来减少维度
        expanded_embedding = expanded_embedding[:target_length]
    elif len(expanded_embedding) < target_length:
        # 如果扩展后的特征少于目标长度，可以通过填充或其他方法来增加维度
        expanded_embedding = np.pad(expanded_embedding, (0, target_length - len(expanded_embedding)))
    return expanded_embedding

#@app.post("/v1/embeddings", response_model=EmbeddingResponse)
#async def get_embeddings(request: EmbeddingRequest, credentials: HTTPAuthorizationCredentials = None):   
#@app.post("/v1/embeddings")
@app.route('/v1/embeddings', methods=['POST']) 
def get_embeddings():   
    
    # 计算嵌入向量和tokens数量
    #print(request.input)
    # if type(request.input) == 'str':
    #     request.input = [request.input] 
    #print(request)
    em_input = request.json.get('input')
    if isinstance(em_input, str):
        em_input_list = [em_input]
    else:
        em_input_list = em_input
    mylogger.debug(f"Get {len(em_input_list)} embedding requests")
    #embeddings = [model.encode(text) for text in request.input]
    #embeddings = [create_embedding_bge(text) for text in request.input]
    embeddings = [create_embedding_bge_np(text) for text in em_input_list]

    # 如果嵌入向量的维度不为1536，则使用插值法扩展至1536维度 
    # embeddings = [interpolate_vector(embedding, 1536) if len(embedding) < 1536 else embedding for embedding in embeddings]
    # 如果嵌入向量的维度不为1536，则使用特征扩展法扩展至1536维度 
    embeddings = [expand_features(embedding, 1536) if len(embedding) < 1536 else embedding for embedding in embeddings]

    # Min-Max normalization
    # embeddings = [(embedding - np.min(embedding)) / (np.max(embedding) - np.min(embedding)) if np.max(embedding) != np.min(embedding) else embedding for embedding in embeddings]
    embeddings = [embedding / np.linalg.norm(embedding) for embedding in embeddings]
    # 将numpy数组转换为列表
    embeddings = [embedding.tolist() for embedding in embeddings]
    #prompt_tokens = sum(len(text.split()) for text in request.input)
    prompt_tokens = sum(len(text.split()) for text in em_input_list)
    total_tokens = 0
    
    response = {
        "data": [
            {
                "embedding": embedding,
                "index": index,
                "object": "embedding"
            } for index, embedding in enumerate(embeddings)
        ],
        #"model": request.model,
        "model": "",
        "object": "list",
        "usage": {
            "prompt_tokens": prompt_tokens,
            "total_tokens": total_tokens,
        }
    }

    mylogger.debug(f"return {len(embeddings)} embeddings")
    return response

@app.route('/register', methods=['POST'])    
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    clear_expired_user_keys()  # 清理过期的userKey

    query = "SELECT * FROM user_info WHERE username=%s"
    db_handler.execute_query(query, (username, ))
    res = db_handler.fetchone()
    if res:
        mylogger.debug(f'{username} existed! Return 405 failure')
        return jsonify({"status": "fail", "message": "用户名已经存在"}), 405
    else:
        query = "INSERT INTO user_info (username, mypwd) VALUES (%s, %s)"
        db_handler.execute_query(query, (username, password))
        mylogger.debug(f'{username} has added to user_info db')
        return jsonify({"status": "success", "message": "注册成功"}), 200

@app.route('/changepwd', methods=['POST'])
def changePassword():
    username = request.json.get('username')
    password = request.json.get('password')
    clear_expired_user_keys()  # 清理过期的userKey

    query = "SELECT id, username FROM user_info WHERE username=%s"
    db_handler.execute_query(query, (username, ))
    res = db_handler.fetchone()
    if res:
        id, _ = res
        query = "UPDATE user_info SET mypwd=%s WHERE username=%s"
        db_handler.execute_query(query, (password, username))
        mylogger.debug(f'{username} {password} change DONE.')
        return jsonify({"status": "success", "message": "密码修改成功成功"}), 200
    else:
        mylogger.debug(f'{username} does not exist! Return 405 failure')
        return jsonify({"status": "fail", "message": "用户名不存在"}), 405

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    clear_expired_user_keys()  # 清理过期的userKey

    if checkUser(username, password):
        # 生成一个随机的session key
        session_key = str(uuid.uuid4())
        
        #query = "DELETE FROM user_session WHERE username = %s"
        #query = "UPDATE user_session SET valid_flag=0 WHERE username=%s"
        #db_handler.execute_query(query, (username,))
        query = "INSERT INTO user_session (userKey, username, valid_flag) VALUES (%s, %s,%s)"
        db_handler.execute_query(query, (session_key, username,1))
                
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
    query = 'SELECT username, last_refresh FROM user_session WHERE userKey = %s'
    db_handler.execute_query(query, (userKey,))
    res = db_handler.fetchone()
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
    query = 'SELECT username, valid_flag, last_refresh FROM user_session WHERE userKey=%s and valid_flag=1'
    db_handler.execute_query(query, (user_key,))
    res = db_handler.fetchone()
    if res:
        username, _, _ = res        
        query = 'UPDATE user_session SET valid_flag=1 WHERE userKey=%s'
        db_handler.execute_query(query, (user_key,))
        return jsonify({"status": "success", "username": username}), 200
    else:
        return jsonify({"status": "fail", "message": "验证失败"}), 401           
    
def generate_float_list():
    float_list = [round(i * 0.01, 2) for i in range(1, 1025)]
    return float_list

def clear_expired_user_keys():    
    # 删除1小时前更新的userKey
    #query = "DELETE FROM user_session WHERE last_refresh < (NOW() - INTERVAL 1 HOUR)"
    query = "UPDATE user_session SET valid_flag=0 WHERE last_refresh < (NOW() - INTERVAL 1 HOUR)"
    db_handler.execute_query(query)

@app.route('/genvec', methods=['POST'])
def get_float_list():
    question = request.json.get('question')
    mylogger.debug(f'Get question: {question}')
    #float_list = generate_float_list()
    float_list = create_embedding_bge(question)
    mylogger.debug(f'Done embedding: {len(float_list)}, {float_list[0]}, {float_list[-1]}')
    return jsonify(float_list)

if __name__ == '__main__':
    # host = 'localhost'
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    host = config['host']
    #print('Start flask  ')
    app.run(debug=False, host=host, port=5111)
    #app.run(debug=True, host='127.0.0.1', port=5201)


# 在实际应用中，还需实现logout等接口，清除对应session_key的数据，并且考虑session过期等问题