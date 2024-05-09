from flask import Flask, request, jsonify
from utilities import logger
from searchCodebase import SearchCodebase
from searchKnowledgebase import SearchKB
from searchRequirement import SearchRequirement
from searchTestcase import SearchTestcase
from copilot import Copilot
from flask_cors import CORS
import json

LOG = logger.Logger(name=logger.SEARCHALL_LOG_FILE_NAME, debug=True).logger

app = Flask(__name__)  
CORS(app)

code_retriever = SearchCodebase()
kb_retriever = SearchKB()
req_retriever = SearchRequirement()
coding_helper = Copilot()
tc_retriever = SearchTestcase()

@app.route('/getProjectList', methods=['GET'])
def get_project_list():
    LOG.debug('Invoke: get_project_list')
    return jsonify(req_retriever.get_project_list())

@app.route('/getProjectList_tc', methods=['GET'])
def get_project_list_TC():
    LOG.debug('Invoke: get_project_list_tc')
    return jsonify(tc_retriever.get_project_list())

@app.route('/searchTC', methods=['POST'])
def searchTestcase():
    question = request.json['question']
    limit = request.json['count']
    #isBP = request.json['bp']
    username = request.json['username']
    threshold = request.json['threshold']
    project = request.json['project']
    code_retriever.create_log(username, "TC", f"{question} {limit} {project} {threshold}")
    LOG.debug(f'Invoke: search_req, {question} {limit} {project} {threshold}')
    return jsonify(tc_retriever.search_tc(request))

@app.route('/searchReq', methods=['POST'])
def searchRequirement():
    question = request.json['question']
    limit = request.json['count']
    isBP = request.json['bp']
    username = request.json['username']
    threshold = request.json['threshold']
    code_retriever.create_log(username, "REQ", f"{question} {limit} {isBP} {threshold}")
    LOG.debug(f'Invoke: search_req, {question} {limit} {isBP}')
    return jsonify(req_retriever.search_req(request))

@app.route('/searchKB', methods=['POST'])
def searchKB():
    question = request.json['question']
    limit_sum = request.json['limit_sum']
    limit_tp = request.json['limit_tp']  
    username = request.json['username']
    code_retriever.create_log(username, "KB", f"{question} {limit_sum} {limit_tp}")
    LOG.debug(f'Invoke: search_knowledge, {question} {limit_sum} {limit_tp}')
    return jsonify(kb_retriever.search_knowledge(request))

@app.route('/searchCode', methods=['POST'])
def searchCode():
    question = request.json['question']
    limit = request.json['count']
    module = request.json['module']
    username = request.json['username']
    code_retriever.create_log(username, "CODE", f"{question} {limit} {module}")
    LOG.debug(f'Invoke: search_code, {question} {limit} {module}')
    return jsonify(code_retriever.search_codebase(request))

@app.route('/getModuleList', methods=['GET'])
def getModuleList():
    #code_retriever.create_log('', "CODE", 'get module list')
    LOG.debug(f"Invoke: getModuleList")
    return jsonify(code_retriever.getModuleList())

@app.route('/ccpilot', methods=['POST'])
def codinghelper():
    task = request.json['tasks']
    model = request.json['models']
    sourceCode = request.json['sourceCode']
    username = request.json['username']
    tmpStr = sourceCode[:100].replace('\n', ' ')
    code_retriever.create_log(username, "COPILOT", f"{task}, {model}, code: ({len(sourceCode)})--> {tmpStr}")
    LOG.debug(f"Invole: copilot, {task}, {model}, code: ({len(sourceCode)})--> {tmpStr}")

    return jsonify(coding_helper.process_query(request))
if __name__ == '__main__':
    # host = 'localhost'
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    host = config['host']
    app.run(debug=False, host=host, port=5009)
