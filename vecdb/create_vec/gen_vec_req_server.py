import requests
import json
import os
from urllib.parse import urlencode
from utilities import logger
from sqlalchemy import Column, Integer, String, Text, Date
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

class Project(Base):
    __tablename__ = 'project_info'

    workspace_id = Column(String(255), primary_key=True)
    name = Column(String(255))
    systems = Column(String(255))
    modify_time = Column(Date)
    extension1 = Column(String(255))
    url = Column(String(255))
    
class BaseStory(Base):
    __tablename__ = 'base_stories'
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    workspace_id = Column(String(255))
    story_id = Column(String(255))
    name = Column(String(512))
    description = Column(Text)
    url = Column(String(255))
    status = Column(String(255))
    developer = Column(String(255))
    creator = Column(String(255))
    finger_print = Column(String(255))
    extension1 = Column(String(255))
    extension2 = Column(String(255))
    extension3 = Column(String(255))
    extension4 = Column(String(255))
    content = Column(Text)
    vector_id = Column(Integer)
    modify_time = Column(Date)
    close_time = Column(Date)
class Story(BaseStory):
    __tablename__ = 'stories'    


class BPStory(BaseStory):
    __tablename__ = 'stories_bp' 
    customer = Column(String(255))
 
story_table = '../stories'
def isBP():
    if 'bp' in story_table:
        return True
    else:
        return False

if isBP():
    #total_stories = local_session.query(BPStory).filter(BPStory.vector_id == None).all()
    total_stories = local_session.query(BPStory).filter(BPStory.vector_id == None).order_by(BPStory.id.asc()).all()
    index = faiss.read_index("../bp_story.faiss")
    # index = faiss.IndexFlatL2(1024)
else:
    total_stories = local_session.query(Story).filter(Story.vector_id == None).all()
    index = faiss.read_index("../story.faiss")
    
length = len(total_stories)
mylogger.debug(f'to process: {len(total_stories)}, size of FAISS: {index.ntotal}')
        
def create_embedding_bge(sentence):
    response = requests.post('http://10.101.9.50:5111/genvec', json={'question': sentence})
    return response.json()

first_file_flg = True
for story in tqdm(total_stories,total=length):  
    if story.vector_id is None or story.vector_id == '':  # 检查vector_id是否为空字符串或None  
        # mylogger.debug(f"Start to process {index.ntotal}/{len(local_session.query(Story).all())}")
        if isBP():
            content = story.name
        else:
            content = '标题：' + story.name + "\n" + '内容：' + story.content
        vec = create_embedding_bge(content)
        story.vector_id = index.ntotal
        index.add(np.array([vec]))    
        local_session.add(story)  # 将更新后的故事添加回session，这样更改才会被保存到数据库中    
        
    if index.ntotal%25 == 0:
        if isBP():
            file_name = f'bp_story_{index.ntotal}.faiss'
        else:
            file_name = f'story_{index.ntotal}.faiss'
        local_session.commit()
        faiss.write_index(index, file_name)
        
        if first_file_flg:
            first_file_flg = False
        else:
            os.remove(last_file_name)
        last_file_name = file_name  
            
local_session.commit()
if isBP():
    faiss.write_index(index, "../bp_story.faiss")
else:
    faiss.write_index(index, "../story.faiss")    

