#from IPython.display import HTML  
#import os
#import mysql.connector
from utilities import logger
from utilities.embedding import create_embedding_bge
from utilities.dbtool import DBHandler
import faiss
import numpy as np
#from flask import Flask, jsonify, request
#import json
#from xinference.client import Client
#from flask_cors import CORS 
#import sys
#from datetime import datetime
import pandas as pd
#import requests

AMP_NUM = 5
LOG = logger.Logger(name=logger.SEARCHALL_LOG_FILE_NAME, debug=True).logger

module_name_mapping = {'N20核算':'atg-accounting',
                        "N20核心":'fcs-coresvc',
                        "N20结算":'stm-settlement',
                        'N20票据网关前置': 'mrt-whp03-bill-gateway-front',
                        'N20票据综合管理': 'mrt-whp03-bill-manager',
                        'N20票据网关': 'mrt-whp03-bill-gateway',
                        'N20票据库存': 'mrt-whp03-bill-stock',
                        'N20同业票据': 'mrt-whp03-bill-interbank',
                        'N20企业票据': 'mrt-whp03-bill-business',
                        'N20票据网银': 'mrt-whp03-bill-ebank',
                        "金云2.0收付款":'jy2-pay_service',
                        '金云2.0账户': 'jy2-cb_service',
                        '金云2.0公共': 'jy2-common',
                        '金云2.0ERP接口': 'jy2-payservice_service',
                        #'金云2.0新票据-公共': 'jy2-nggds_service',
                        '金云2.0新票据': 'jy2-ngecd_service'}


class SearchCodebase:
    def __init__(self) -> None:     
        self.method_index = faiss.read_index('vecdb/method_embedding.index')  
        self.db = DBHandler('codebase')
        errflg, errmsg = self.db.geterror()
        LOG.debug(errmsg)
        LOG.debug(f"Open FAISS db with {self.method_index.ntotal} entires, cover {module_name_mapping.keys()}")
        if not errflg:
            raise Exception("An error occurred: " + errmsg)

    def getModuleList(self):
        results = []
        for module in list(module_name_mapping.keys()):
            results.append({'label':module, 'value':module})
        return results
        
    def create_log(self, username, type, question):
        query = 'INSERT INTO qlog (username, type, question) VALUES (%s,%s,%s)'
        self.db.execute_query(query, (username, type, question))
        
    def query(self, question, limit, module_list, threshold):
        LOG.debug("Start to create embedding of question ...")
        query_vec = create_embedding_bge(question)       

        id_list = []
        LOG.debug("Start to search FAISS db ...")
        distances, indices = self.method_index.search(np.array([query_vec], dtype=np.float32), limit)
        LOG.debug(f'Complete FAISS DB search, get {limit} entries')
        results = []
        res_count = 1
        for i in range(limit):
            index = indices[0][i]
            distance = distances[0][i]    
            if float(distance) > threshold:
                LOG.debug(f'{i} Distance is beyond threshold, break, {distance} > {threshold}')
                break             
            
            #query = "SELECT package, class, method, com_all, content, file_path, class_type, module FROM method_info WHERE vector_id=%s and module in (%s)"
            query = "SELECT package, class, method, com_all, content, file_path, class_type, module FROM method_info WHERE vector_id=%s"
            self.db.execute_query(query, (int(index),))
            record = self.db.fetchone()

            if record:                
                package,class_name,method, com_all, content, file_path, class_type, module = record
                if module in module_list:
                    git_path = f"https://e.gitee.com/nstc/repos/nstc/{module_name_mapping[module]}/blob/master/"    
                    local_path = f"E:/repo/{module_name_mapping[module]}//"
                    res = {
                        'Package': f'[{distance:.8f}] {package}',
                        'Method':f"{class_name}.{method}",
                        'Comment':com_all,
                        'Content':content,
                        'URL':file_path.replace(local_path, git_path),
                        'Distance':distance,
                        'Type': class_type,
                        'Module': module
                    }
                    debug_str = com_all.replace('\n', '...')
                    LOG.debug(f"Result {res_count}> Distance:{distance}, {module}.{package}.{class_name}.{method}, [{debug_str[:30]}]")      
                    res_count += 1         
                    
                    results.append(res)
                    id_list.append(index)

                    if res_count >= limit/AMP_NUM:
                        break

        return results, id_list

    def create_debug_result(self) -> list:
        test_res = []
        df = pd.read_excel('all_output_comments_final.xlsx')
        for idx, item in df.iterrows():
            test_res.append({
                'ID':idx+1,
                'Package':f"com.nstc.{item['class']}.{item['method']}",
                'Method':f"{item['class']}.{item['method']}",
                'Comment':item['deepSeek'],
                'Content':item['function'],
                'URL': f"https://www.baidu.com/{item['method']}"
            })
        
        return test_res

 
    def search_codebase(self, request):  
        #LOG.debug(f"{type(request)}: {request.json}")
        question = request.json['question']
        limit = request.json['count']
        module = request.json['module']
        threshold = request.json['threshold']

        LOG.debug(f"get question: {question}, limit: {limit}, module: {module}, threshold-{threshold}")  
        matches, id_list = self.query(question, limit*AMP_NUM, module, threshold)

        results = []
        #matches = create_debug_result()
        for idx, match in enumerate(matches, start=1):
            #url_str = f'https://www.tapd.cn/{match.workspace_id}/prong/stories/view/{match.story_id}'
            #url_str = 'https://www.baidu.com'
            res = {
                'ID' : idx,
                'Package' : match['Package'],
                'Method' : match['Method'],
                'Comment' : match['Comment'],
                'Content' : match['Content'],
                #'URL' : match.url
                'URL' : match['URL'],
                'Distance': float(match['Distance']),
                'Type': match['Type'],
                'Module': match['Module']
            }       

            results.append(res)

        # register log
        # record ={}
        # record['question'] = question
        # record['query'] = "BP " + str(isBP)
        # record['answer'] = f'{id_list}'
        # record['stime'] = datetime.now().date()
        # local_session.add(Log(**record))
        # local_session.commit()
        #     
        # results = test_res
        LOG.debug(f"------------------> return {len(results)} answers <--------------------")
        #return jsonify(results)
        return results

# if __name__ == '__main__':  
#     #host = 'localhost'    
#     host = '10.101.9.50'
#     app.run(debug=False, port=5009, host=host)
if __name__ == '__main__':
    engine = SearchCodebase()
