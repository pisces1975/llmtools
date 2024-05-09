import requests
import json
import os
from urllib.parse import urlencode
from utilities import logger
from sqlalchemy import Column, Integer, String, Text, Date, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import time
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import faiss
import numpy as np
import shutil
from tqdm import tqdm 
import requests

mylogger = logger.Logger(name='create_vec', debug=True).logger

def create_embedding_bge(sentence):
    response = requests.post('http://10.101.9.50:5111/genvec', json={'question': sentence})
    return response.json()

# 创建基础类
Base = declarative_base()

username = 'root'
password = 'newpass'
host = "127.0.0.1"
#host = '10.101.9.50'
dbname = 'requirements'
engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}/{dbname}")
Session = sessionmaker(bind=engine)
local_session = Session()

try:
    # 连接数据库，并执行一个简单查询
    connection = engine.connect()
    result = connection.execute("SELECT 1")
    
    # 打印结果
    mylogger.debug(f"Database connection successful. Result: {result.scalar()}")
    
    # 不要忘记关闭连接！
    connection.close()
    
except Exception as e:
    mylogger.error(f"Database connection failed. Error: {e}")

class TCase(Base):
    __tablename__ = 'tcases'

    id = Column(Integer, primary_key=True)
    workspace_id = Column(String(255), nullable=False)
    tcase_id = Column(String(255), nullable=False)
    category_id = Column(String(255), nullable=False)
    name = Column(Text, nullable=False)
    steps = Column(Text)
    precondition = Column(Text)
    expectation = Column(Text)
    URL = Column(String(255))
    finger_print = Column(String(255))
    content = Column(Text)
    type = Column(Text)
    vector_id = Column(Integer)
    updated_at = Column(TIMESTAMP)
    
 

total_stories = local_session.query(TCase).filter(TCase.vector_id == None).all()
#index = faiss.read_index("../testcases.faiss")
index = faiss.IndexFlatL2(1024)
    
length = len(total_stories)
mylogger.debug(f'to process: {len(total_stories)}, size of FAISS: {index.ntotal}')
        
first_file_flg = True

for story in tqdm(total_stories,total=length):  
    if story.vector_id is None or story.vector_id == '':  # 检查vector_id是否为空字符串或None          
        vec = create_embedding_bge(story.content)
        story.vector_id = index.ntotal
        index.add(np.array([vec]))    
        local_session.add(story)  # 将更新后的故事添加回session，这样更改才会被保存到数据库中    
        
    if index.ntotal%25 == 0:
        file_name = f'testcases_{index.ntotal}.faiss'
        local_session.commit()
        faiss.write_index(index, file_name)
        
        if first_file_flg:
            first_file_flg = False
        else:
            os.remove(last_file_name)

        last_file_name = file_name  
            

local_session.commit()
#file_name = f'testcases_{index.ntotal}.faiss'
#faiss.write_index(index, file_name)
faiss.write_index(index, "../testcases.faiss")