import uuid
from flask import Flask, request, jsonify
from utilities import logger
from flask_cors import CORS
import sys
from xinference.client import Client
import mysql.connector
import json
from utilities.dbtool import DBHandler
import numpy as np
from pydantic import BaseModel
from typing import List
from scipy.interpolate import interp1d
from sklearn.preprocessing import PolynomialFeatures
#from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
#app = Flask(__name__)
mylogger = logger.Logger(name='llmtool', debug=True).logger  
app = Flask(__name__)  
CORS(app)

@app.route('/v1/embeddings', methods=['POST']) 
def get_embeddings(): 
    return 'success'


if __name__ == '__main__':
    # host = 'localhost'
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    host = config['host']
    print('Start flask  ')
    #app.run(debug=False, host=host, port=5111)
    app.run(debug=True, host='127.0.0.1', port=5201)