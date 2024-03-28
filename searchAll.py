from flask import Flask, request, jsonify
from utilities import logger
from searchCodebase import SearchCodebase
from searchKnowledgebase import SearchKB
from searchRequirement import SearchRequirement
from flask_cors import CORS
import json

LOG = logger.Logger(name=logger.SEARCHALL_LOG_FILE_NAME, debug=True).logger

app = Flask(__name__)  
CORS(app)

code_retriever = SearchCodebase()
kb_retriever = SearchKB()
req_retriever = SearchRequirement()

@app.route('/getProjectList', methods=['GET'])
def get_project_list():
    LOG.debug('Invoke: get_project_list')
    return jsonify(req_retriever.get_project_list())

@app.route('/searchReq', methods=['POST'])
def searchRequirement():
    question = request.json['question']
    limit = request.json['count']
    isBP = request.json['bp']
    LOG.debug(f'Invoke: search_req, {question} {limit} {isBP}')
    return jsonify(req_retriever.search_req(request))

@app.route('/searchKB', methods=['POST'])
def searchKB():
    question = request.json['question']
    limit_sum = request.json['limit_sum']
    limit_tp = request.json['limit_tp']  
    LOG.debug(f'Invoke: search_knowledge, {question} {limit_sum} {limit_tp}')
    return jsonify(kb_retriever.search_knowledge(request))

@app.route('/searchCode', methods=['POST'])
def searchCode():
    question = request.json['question']
    limit = request.json['count']
    module = request.json['module']
    LOG.debug(f'Invoke: search_knowledge, {question} {limit} {module}')
    return jsonify(code_retriever.search_codebase(request))

if __name__ == '__main__':
    # host = 'localhost'
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    host = config['host']
    app.run(debug=False, host=host, port=5009)
