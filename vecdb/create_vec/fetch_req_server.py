import requests
import json
import os
from urllib.parse import urlencode
from utilities import logger
import mysql.connector
from utilities.sha_tools import generate_sha_digest
from sqlalchemy import Column, Integer, String, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import time
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime

api_user = 'h=Czxr?m'

api_password = 'B537AF1C-64F9-FB2D-DC31-1E8C334E8D79'
mylogger = logger.Logger(name='TAPD_ana', debug=True).logger

def html_to_text(html):
    if not html or len(html) == 0:
        return ''
    
    #"抛弃HTML标签，只提取所有文本内容"
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    return text

# 创建基础类
Base = declarative_base()

username = 'root'
password = 'newpass'
#host = "127.0.0.1"
host = '10.101.9.50'
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
 
def insert_or_update_data(session, record):
    if isBP():
        # 查询是否存在 story_id 相同的 BPStory 记录
        existing_story = session.query(BPStory).filter_by(story_id=record['story_id']).first()
        if existing_story:
            # 更新已有记录
            record['extension1'] = 'UPDATE'
            for key, value in record.items():
                setattr(existing_story, key, value)
        else:
            # 创建新的 BPStory 记录
            record['extension1'] = 'ADD'
            existing_story = BPStory(**record)
    else:
        # 查询是否存在 story_id 相同的 Story 记录
        existing_story = session.query(Story).filter_by(story_id=record['story_id']).first()
        if existing_story:
            # 更新已有记录
            record['extension1'] = 'UPDATE'
            for key, value in record.items():
                setattr(existing_story, key, value)
        else:
            # 创建新的 Story 记录
            record['extension1'] = 'ADD'
            existing_story = Story(**record)

    # 添加（或更新后相当于添加）记录到 session，并提交事务
    session.add(existing_story)
    session.commit()

def insert_or_update_story_db(items):
    total = len(items)
    for story in tqdm(items, total=total):
        # if story['workspace_id'] not in complete_wid:
        #     continue
        record = {}
        record['workspace_id'] = story['workspace_id']
        record['story_id'] = story['id']
        record['name'] = story['name']
        record['creator'] = story['creator']
        record['status'] = story['status']
        record['developer'] = story['developer']
        if story['description']: 
            record['description'] = story['description'][:3000] 
        else: 
            record['description'] = ''
        record['url'] = f"https://www.tapd.cn/{record['workspace_id']}/prong/stories/view/{record['story_id']}"
        record['content'] = html_to_text(record['description'])
        record['finger_print'] = generate_sha_digest(record['content'])
        record['modify_time'] = story['modified']
        if story['completed']:
            record['close_time'] = story['completed']
        else:
            record['close_time'] = '2100-01-01'
        
        if isBP():        
            record['customer'] = story['custom_field_one']
        
        insert_or_update_data(local_session, record) 

def update_story_status(ids, status):
    total = len(ids)
    for story_id in tqdm(ids, total=total): 
        if isBP():
            # 更新 BPStory 表中 story_id 对应记录的 extension1 字段
            local_session.query(BPStory).filter_by(story_id=story_id).update({"extension1": status})
        else:
            # 更新 Story 表中 story_id 对应记录的 extension1 字段
            local_session.query(Story).filter_by(story_id=story_id).update({"extension1": status})

    # 提交事务
    local_session.commit()

result_query  = local_session.query(Project.workspace_id).filter(Project.modify_time < '2024-3-15')
project_list = result_query.all()
mylogger.debug(f"{len(project_list)} projects to analyze, {project_list[0][0]} ... {project_list[-1][0]}")



sum = 0
base_url = "https://api.tapd.cn/stories"
page_to_break = 0
item_list_original = []
item_to_update = []
item_to_analyze = []

analyse_res = []
complete_wid = set()
i = 1

for row in project_list:   
    wid = row[0]
    id_to_keep = []
    id_to_add = []
    id_to_update = []

    if wid == '62366085' or wid == '39451937':
        story_table = '../bp_stories'  
        continue  
    else:
        story_table = '../stories'   

    try:
        r = requests.get(f"https://api.tapd.cn/stories/count?workspace_id={wid}", auth=(api_user, api_password))
        ret = r.text # 获取接口返回结果
        # print(ret) # Python 3
        json_string = json.loads(ret)
        total_entries = json_string['data']['count']
        pinfo = local_session.query(Project.name).filter(Project.workspace_id == wid).first()
        prj_name = pinfo[0]
        # mylogger.info(f'{wid} {prj_name}, {total_entries}')
        sum += total_entries
    except Exception as e:
        mylogger.error(f"{wid} {prj_name} Something goes wrong {e}")    
        continue

    current_page = 1    
    if total_entries >= 1000:
        batch_size = 200
    else:
        batch_size =100
    current_index = 0
    item_number = 0    

    current_batch = []
    mylogger.debug(f"{i}/{len(project_list)} Start to process {wid} {prj_name} {total_entries} entries")
    while current_index < total_entries:
        mylogger.debug(f">>>>>>>>>>Fetch page #{current_page}")
        params = {
            "workspace_id": wid,
            "page": current_page,
            "limit": batch_size
        }

        query_string = urlencode(params)
        full_url = f"{base_url}?{query_string}"
        
        r = requests.get(full_url, auth=(api_user, api_password))
        # r = requests.get(f"https://api.tapd.cn/tapd_wikis?workspace_id={workspace_id}", auth=(api_user, api_password))
        ret = r.text # 获取接口返回结果
        decoded_data = json.loads(ret)
        if(decoded_data['status'] != 1):
            mylogger.error(decoded_data)
            break
        else:
            story_entries = decoded_data["data"]
            #mylogger.debug(f"number of wiki pages are {len(story_entries)}")
            index = 1
            for entry in story_entries:
                story = entry["Story"]
                item_to_analyze.append(story)
                result = local_session.query(Story).filter(Story.story_id == story['id']).first()
                if result:
                    ID = result.story_id
                    finger_print =result.finger_print    
                    sha_digest = generate_sha_digest(html_to_text(story["description"]))
                    if finger_print == sha_digest:
                        #mylogger.debug(f"story {ID} already exist, content is the same")
                        id_to_keep.append(ID)
                        pass
                    else:
                        #mylogger.debug(f"story {ID} already exist, but content is different")  
                        item_to_analyze.append(story)             
                        id_to_update.append(ID)
                        current_batch.append(story)
                else:
                    #mylogger.info(f"{story['id']} {story['name']} should be added")
                    item_to_update.append(story)   
                    current_batch.append(story)
                    id_to_add.append(story['id'])

            current_index += batch_size
            current_page += 1
            page_to_break += 1
            # if current_page >= 2:
            #     break
            time.sleep(1)
            if current_page % 10 == 0:
                time.sleep(20)  

    mylogger.debug(f"{wid} {prj_name}, {len(id_to_keep)} keep,  {len(id_to_add)} add, {len(id_to_update)} update")
    insert_or_update_story_db(current_batch)
    
    update_story_status(id_to_keep,'KEEP')    
    local_session.query(Project).filter_by(workspace_id=wid).update({"modify_time": datetime.now()})
    analyse_res.append({
        'wid':wid,
        'project':prj_name,
        'keep':id_to_keep,
        'add':id_to_add,
        'update':id_to_update
    })
    #complete_wid.add(wid)  
    i += 1
    time.sleep(5) 
                 
for idx, item in enumerate(analyse_res, start=1):
    mylogger.debug(f"{idx}/{len(analyse_res)}. {item['wid']}-{item['project']}, {len(item['keep'])} keep, {len(item['add'])} add, {len(item['update'])} update")
    