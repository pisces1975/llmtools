#from IPython.display import HTML  
#import os
#import mysql.connector
from utilities import logger
from utilities.embedding import create_embedding_bge
from utilities.dbtool import DBHandler
import faiss
import numpy as np
#from flask import Flask, jsonify, request
import json
#from xinference.client import Client
#from flask_cors import CORS 
import sys
#from datetime import datetime
#import pandas as pd
#import requests
LOG = logger.Logger(name=logger.SEARCHALL_LOG_FILE_NAME, debug=True).logger

class SearchKB:
    def __init__(self) -> None:
        self.summary_index = faiss.read_index('vecdb/bge_ms_index_summary.faiss')  
        self.textpoint_index = faiss.read_index('vecdb/bge_ms_index_textpoints.faiss')  
        self.db = DBHandler('knowledgebase')
        errflg, errmsg = self.db.geterror()
        LOG.debug(errmsg)
        LOG.debug(f"Open FAISS db with s-{self.summary_index.ntotal} entires, t-{self.textpoint_index.ntotal} entries")
        if not errflg:
            raise Exception("An error occurred: " + errmsg)

    def query(self, question, limit_sum, limit_tp, threshold):
        LOG.debug("Start to create embedding of question ...")
        query_vec = create_embedding_bge(question)   

        id_list = []
        results = []
        LOG.debug("Start to search FAISS db ...")
        if limit_sum > 0:
            distances, indices = self.summary_index.search(np.array([query_vec], dtype=np.float32), limit_sum)
            LOG.debug(f'Complete FAISS DB search, get {limit_sum} entries')
            for i in range(limit_sum):
                index = indices[0][i]
                distance = distances[0][i]     
                if float(distance) > threshold:
                    LOG.debug(f'{i} Distance is beyond threshold, break, {distance} > {threshold}')
                    break
                query = "SELECT ID, name, description, full_path, URL FROM knowledgebase WHERE vector_id=%s"
                self.db.execute_query(query, (int(index), ))
                record = self.db.fetchone()    
                if record:
                    ID, name, description, full_path, URL = record
                    if len(description) < 5:
                        LOG.error(f"too short content, WIKI, {ID}, {index}, {name}")
                    item = {
                        'name': name,
                        'content': description,
                        'type': 'summary',
                        'full_path': full_path,
                        'URL': URL,
                        'distance': float(distance)
                    }        
                    results.append(item)
                    id_item = {
                        'id': int(index),
                        'type': 'summary'
                    }
                    id_list.append(id_item)
        if limit_tp > 0:
            distances, indices = self.textpoint_index.search(np.array([query_vec], dtype=np.float32), limit_tp)
            LOG.debug(f'Complete FAISS DB search, get {limit_tp} entries')
            for i in range(limit_tp):
                index = indices[0][i]
                distance = distances[0][i]   
                if float(distance) > threshold:
                    LOG.debug(f'{i} Distance is beyond threshold, break, {distance} > {threshold}')
                    break  
                query = "SELECT id, wiki_id, content FROM textpoints_1204 WHERE vector_id=%s"
                self.db.execute_query(query, (int(index), ))
                record = self.db.fetchone()    
                if record:
                    id, wiki_id, content = record
                    query = "SELECT name, full_path, URL FROM knowledgebase WHERE ID=%s"
                    self.db.execute_query(query, (wiki_id, ))
                    rec = self.db.fetchone()
                    if rec:
                        name, full_path, URL = rec
                        if len(content) < 5:
                            LOG.error(f"too short content, textpoint, {id}, {wiki_id}, {name}")
                        item = {
                            'name': name,
                            'content': content,
                            'type': 'textpoint',
                            'full_path': full_path,
                            'URL': URL,
                            'distance': float(distance)
                        }        
                        results.append(item)
                        id_item = {
                            'id': int(index),
                            'type': 'textpoint'
                        }
                        id_list.append(id_item)   

        return results, id_list


    def search_knowledge(self, request):  
        #LOG.debug(f"{type(request)}: {request.json}")
        question = request.json['question']
        limit_sum = request.json['limit_sum']
        limit_tp = request.json['limit_tp']    
        threshold = request.json['threshold']

        LOG.debug(f"get question: {question}, limit_sum-{limit_sum}, limit_tp-{limit_tp}, threshold-{threshold}")  
        matches, id_list = self.query(question, limit_sum, limit_tp, threshold)

        results = []
        #matches = create_debug_result()
        for idx, match in enumerate(matches, start=1):
            #url_str = f'https://www.tapd.cn/{match.workspace_id}/prong/stories/view/{match.story_id}'
            #url_str = 'https://www.baidu.com'
            res = {
                'ID' : idx,
                'name' : match['name'],
                'content' : match['content'],
                'full_path' : match['full_path'],
                'type' : match['type'],            
                'URL' : match['URL'],
                'distance': match['distance']            
            }       

            results.append(res)

        LOG.debug(f"------------------> return {len(results)} answers <--------------------")
        #return jsonify(results)
        return results

# if __name__ == '__main__':  
#     with open('config.json', 'r') as config_file:
#         config = json.load(config_file)

#     host = config['host']
#     app.run(debug=False, port=5010, host=host)
if __name__ == '__main__':
    engine = SearchKB()