from flask import Flask, request, jsonify
from utilities.logger import LOG
from searchCodebase import SearchCodebase
from searchKnowledgebase import SearchKB
from searchRequirement import SearchRequirement
from flask_cors import CORS
import json

app = Flask(__name__)  
CORS(app)

code_retriever = SearchCodebase()
kb_retriever = SearchKB()
req_retriever = SearchRequirement()

@app.route('/getProjectList', methods=['GET'])
def get_project_list():
    return jsonify(req_retriever.get_project_list())

@app.route('/searchReq', methods=['POST'])
def searchRequirement():
    return jsonify(req_retriever.search_req(request))

@app.route('/searchKB', methods=['POST'])
def searchKB():
    return jsonify(kb_retriever.search_knowledge(request))

@app.route('/searchCode', methods=['POST'])
def searchCode():
    return jsonify(code_retriever.search_codebase(request))

if __name__ == '__main__':
    # host = 'localhost'
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    host = config['host']
    app.run(debug=False, host=host, port=5009)
