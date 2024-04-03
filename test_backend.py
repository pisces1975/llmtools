from flask import Flask, request, jsonify
from utilities import logger
from utilities.embedding import create_embedding_bge
from utilities.dbtool import DBHandler
from flask_cors import CORS
app = Flask(__name__)
dbh = DBHandler('knowledgebase')
CORS(app)

@app.route('/query', methods=['POST'])
def query():
    
    data = request.get_json()
    value = data.get('value')
    
    # 在这里处理数值并返回文本
    # 假设我们简单地将数值拼接到一个HTML链接中返回
    #response_text = f'<a href="https://example.com">{value}</a>'
    #query = 'SELECT content '
    response_text = """
        测试文字第一段
        <a href='https://www.tapd.cn/tfl/pictures/202309/tapd_36446663_1695622032_284.png'>pic</a>
        测试文字第二段 <a href='https://www.tapd.cn/tfl/pictures/202309/tapd_36446663_1695619791_621.png'>pic2</a> 后半部分
    """

    response_text = '''
        [toc]
##版本信息
[[ 修订日期 | 版本号 | 描述 | 作者 |]][[ 2021-10-09 | 0.1 | 初稿 | 胡司京  |]]
##1. 目的和适用范围
为了标准化外汇业务流程，提高工作效率，更好、更快、更准确的完成业务测试和联调测试，成功上线系统，特制定此流程。本流程适用于N6系统里结售汇系统、外管局数据采集和外汇账户管理模块。完成结售汇业务和外管局数据采集并上报的测试工作。
整体业务流程如下
![Pic1 #600px]<a href="https://www.tapd.cn/tfl/pictures/202110/tapd_36446663_1634796476_35.png" target="_blank">示意图</a>
    'content': row['content'].replace(' ',' '), '''
    return jsonify({'text': response_text})

if __name__ == '__main__':
    app.run(port=5122)