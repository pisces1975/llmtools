#import streamlit as st  
#import pandas as pd  
#from IPython.display import HTML  
#import os
#os.chdir('c:/repo/Knowledgebase-Robot/')
#from utilities import logger
from utilities import logger
from utilities.embedding import create_embedding_bge
from utilities.dbtool import DBHandler
#from sqlalchemy import Column, Integer, String, Text, Date
#from sqlalchemy.ext.declarative import declarative_base
#from sqlalchemy import create_engine
#from sqlalchemy.orm import sessionmaker
import faiss
import numpy as np
#from flask import Flask, jsonify, request
import json
#from xinference.client import Client
from flask_cors import CORS 
#import sys
from datetime import datetime
#import mysql.connector
#import requests
import json

LOG = logger.Logger(name=logger.SEARCHALL_LOG_FILE_NAME, debug=True).logger

class SearchTestcase:
    def __init__(self) -> None:      
        self.story_index = faiss.read_index('vecdb/testcases.faiss')  
        #self.bp_index = faiss.read_index('vecdb/bp_story.faiss')
        self.db = DBHandler('requirements')
        errflg, errmsg = self.db.geterror()
        LOG.debug(errmsg)
        LOG.debug(f"Open FAISS db with {self.story_index.ntotal} entires")
        if not errflg:
            raise Exception("An error occurred: " + errmsg)

    def lookup_vec(self, question, limit=10, project='', threshold=0.9):
        LOG.debug("Start to create embedding of question ...")
        query_vec = create_embedding_bge(question)
        id_list = []
        LOG.debug("Start to search FAISS db ...")
        distances, indices = self.story_index.search(np.array([query_vec], dtype=np.float32), limit)
        LOG.debug(f'Complete FAISS DB search, get {limit} entries')
        results = []
        for i in range(limit):
            index = indices[0][i]
            distance = distances[0][i]      
            if float(distance) > threshold:
                LOG.debug(f'{i} Distance is beyond threshold, break, {distance} > {threshold}')
                break           
            
                #query_condition = Story.vector_id == index  
                #res = local_session.query(Story).filter(query_condition).all()  
            query = "SELECT workspace_id, category_id, name, steps, precondition, expectation, URL, type, updated_at, content FROM tcases WHERE vector_id = %s"
            self.db.execute_query(query, (int(index),))
            res = self.db.fetchone()
            workspace_id, category_id, name, steps, precondition, expectation, URL, tctype, updated_at, content = res
            project_info, systems = self.get_project_name(workspace_id)
            category = self.get_category_name(category_id)
            if project and len(project) > 0:
                if project not in systems:
                    continue
            item = {
                'project' : project_info,                
                'name' : name,                
                'content' : content,
                'category' : category,
                'type' : tctype,
                'URL' : URL,
                'steps' : steps,
                'precondition' : precondition,
                'expectation' : expectation,
                'modify_time' : updated_at,   
                'distance' : distance
            }
            
            LOG.debug(f"Result {i + 1}> Distance:{distance}, index:{index}, Content:{item['name']}")      
            results.append(item)
            id_list.append(index)

        return results, id_list

    def get_category_name(self, cid):
        #pinfo = local_session.query(Project.name).filter_by(workspace_id=wid).first()
        query = "SELECT name FROM tcase_categories WHERE category_id = %s"
        self.db.execute_query(query, (cid,))
        pinfo = self.db.fetchone()
        if pinfo:
            return pinfo[0]
        else:
            LOG.debug(f"Could not find category name for {cid}")
            return '不确定'
        
    def get_project_name(self, wid):
        #pinfo = local_session.query(Project.name).filter_by(workspace_id=wid).first()
        query = "SELECT name, systems FROM project_info WHERE workspace_id = %s"
        self.db.execute_query(query, (wid,))
        pinfo = self.db.fetchone()
        if pinfo:
            return pinfo[0], pinfo[1]
        else:
            LOG.debug(f"Could not find project name for {wid}")
            return '不确定','不确定'
    
#@app.route('/getList', methods=['GET'])
    def get_project_list(self):
        # options = [{'value': k, 'label': v} for k, v in get_project_list()]    
        # LOG.debug(options)
        LOG.debug(f"Start to query project list ...")
        #pinfo = local_session.query(Project).all()
        query = "SELECT workspace_id, name, systems, modify_time, extension1, url FROM project_info WHERE tc_flag=1"
        self.db.execute_query(query)
        pinfo = self.db.fetchall()

        project_list = []
        
        for idx, p in enumerate(pinfo, start=1):
            workspace_id, name, systems, modify_time, extension1, url = p        
            res = {
                '序号' : idx,
                'ID' : workspace_id,
                '名称' : name,
                '系统' : systems,
                '更新时间' : modify_time.strftime("%Y-%m-%d"),
                'URL' : url,
                '管理员': extension1
            }
            project_list.append(res)

        LOG.debug(f"Get {len(project_list)} project info")
        #return jsonify(project_list)
        return project_list
  
#@app.route('/query', methods=['POST','GET'])  
    def search_tc(self, request):  
        #LOG.debug(f"{type(request)}: {request.json}")
        question = request.json['question']
        limit = request.json['count']
        project = request.json['project']
        threshold = request.json['threshold']
        # if bpflag == 'true'.lower():
        #     isBP = True
        # else:
        #     isBP = False

        LOG.debug(f"get question: {question}, limit: {limit}, project: {project}, threshold-{threshold}")  
        matches, id_list = self.lookup_vec(question, limit, project, threshold)

        # item = {
        #         'project' : project_info,                
        #         'name' : name,                
        #         'content' : content,
        #         'category' : category,
        #         'type' : tctype,
        #         'URL' : URL,
        #         'steps' : steps,
        #         'precondition' : precondition,
        #         'expectation' : expectation,
        #         'modify_time' : updated_at,                
        #     }
        results = []
        for idx, match in enumerate(matches, start=1):
            #url_str = f"https://www.tapd.cn/{match['workspace_id']}/prong/stories/view/{match['story_id']}"
            #project_info, _ = self.get_project_name(match['workspace_id'])
            res = {
                'id' : idx,
                'project' : match['project'],                
                'name' : match['name'],
                'steps' : match['steps'],
                'category' : match['category'],
                'precondition' : match['precondition'],
                'expectation' : match['expectation'],
                'content' : match['content'].replace("用例步骤如下：", "【用例步骤如下】").replace("用例名称是：", "【用例名称】"),
                #'URL' : match.url
                'URL' : match['URL'],
                'distance' : float(match['distance'])
            }
            
            results.append(res)

        # register log
        # record ={}
        # record['question'] = question
        # record['query'] = "BP " + str(isBP)
        # record['answer'] = f'{id_list}'
        # record['stime'] = datetime.now().date()
        #local_session.add(Log(**record))
        #local_session.commit()
        query = "INSERT INTO log (question, query, answer, stime) VALUES (%s,%s,%s,%s)"
        self.db.execute_query(query, (question, str(project), f'{id_list}', datetime.now().date()))    

        test_res = [
            {'序号':1, '项目':'Project1', '需求顾问':'张三', '标题':'标题123', '内容':'内容1234阿道夫\n安定坊12电池安多夫', 'URL':'http://abc.com/q'},
            {'序号':2, '项目':'Project2', '需求顾问':'张三', '标题':'标题123', '内容':'内容1234阿道夫\n安定坊12电池地方根本', 'URL':'http://abc.com/q'},
            {'序号':3, '项目':'Project3', '需求顾问':'张三', '标题':'标题123', '内容':'内容1234阿道夫\n安定坊12电池\n111111111111111111111111111111111111111111111122222222222222222', 'URL':'http://abc.com/q'},
            {'序号':4, '项目':'项目4', '需求顾问':'张三123456', '标题':'标题123', '内容':'内容1234阿道夫\n安定坊12电池', 'URL':'https://www.baidu.com'}
        ]
        # results = test_res
        LOG.debug(f"------------------> return {len(id_list)} answers <--------------------")
        #return jsonify(results)
        return results

if __name__ == '__main__':
    engine = SearchTestcase()
