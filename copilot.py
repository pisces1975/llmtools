from IPython.display import HTML  
import os
#os.chdir('c:/repo/Knowledgebase-Robot/')
from utilities import logger
from utilities.strings import system_string
#from utilities.accessGPT import get_feedback_GPT
from utilities.accessBaidu import get_feedback_Baidu
from utilities.accessDeepSeek import get_feedback_Deepseek
from utilities.accessAZure import get_feedback_AZure
from utilities.accessSpark import get_feedback_Spark
# from sqlalchemy import Column, Integer, String, Text, Date
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# import faiss
# import numpy as np
#from flask import Flask, jsonify, request
import json
# from xinference.client import Client
#from flask_cors import CORS 
import sys
from datetime import datetime

mylogger = logger.Logger(name=logger.SEARCHALL_LOG_FILE_NAME, debug=True).logger
#mylogger = logger.Logger(name='copilot', debug=True).logger  
#app = Flask(__name__)  
#CORS(app)

class Copilot:
    def __init__(self):
        pass
    #@app.route('/ccpilot', methods=['POST','GET'])  
    def process_query(self, request):      
        task = request.json['tasks']
        model = request.json['models']
        sourceCode = request.json['sourceCode']
    # if bpflag == 'true'.lower():
    #     isBP = True
    # else:
    #     isBP = False

        #tmpStr = sourceCode_preview = sourceCode[:100].replace('\n', ' ')
        #mylogger.debug(f"get task: {task}, model: {model}, code: ({len(sourceCode)})--> {tmpStr}")  
        if model == 'gpt35':
            # feedback = get_feedback_GPT(system_string[task],sourceCode)
            feedback = get_feedback_AZure(system_string[task],sourceCode)
        elif model == 'ernie':
            feedback = get_feedback_Baidu(system_string[task],sourceCode)
        elif model == 'deepSeek':
            feedback = get_feedback_Deepseek(system_string[task],sourceCode)
        else:
            feedback = get_feedback_Spark(system_string[task],sourceCode)

        #return jsonify('来自大模型的反馈：\n'+ feedback)
        return '来自大模型的反馈：\n'+ feedback

# if __name__ == '__main__':  
#     host = 'localhost'    
#     #host = '10.101.9.50'
#     app.run(debug=True, port=5004, host=host)

