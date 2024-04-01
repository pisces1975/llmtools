from tenacity import retry, wait_random_exponential, stop_after_attempt
import json
import requests
from utilities import logger
mylogger = logger.Logger(name='copilot', debug=True).logger 
#from utilities.ConfigReader import Config
import tiktoken
import time
#from utilities.constants import CONST

timeout = 300
model_name = 'gpt-3.5-turbo'

def get_access_token():
    """
    使用 AK, SK 生成鉴权签名 Access Token 
    :return: access_token, 或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", 
            "client_id": 'GEkIBc9D4RjGMMR40wTkKxPp', 
            "client_secret": 'MYxu0QD6c9kaPGhzuL0UQTVG5UhhwN8I'}
    return str(requests.post(url, params=params).json().get("access_token"))

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def get_feedback_Baidu(system_string, code):   
    headers = {
            "Content-Type": "application/json"
        }
    
    messages = []
    
    payload = json.dumps({
            "temperature": 0.9,
            "system": system_string,
            "messages": [
            {
                "role": "user",
                "content": code
            }]
        }) 
            
    start_time = time.time()  
    
    try:
        URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token=" + get_access_token()     

        mylogger.debug('------------------ Start to query ERNIE 4.0....')
        response = requests.request("POST", URL, headers=headers, data=payload)
        end_time = time.time()  
        run_time = end_time - start_time 
        data = json.loads(response.text) 
        result = data['result']  
        # total_tokens = data['usage']['total_tokens']  
        # fee = (total_tokens / 1000) * Config.get_config_ERNIE4_price()
        # LOG.info("Get chat answer in：{:.2f}秒".format(run_time) + ", expense：{:.5f}分".format(fee))
        tmpStr = result[:50].replace('\n', '  ')
        mylogger.debug(f'Get answer {len(result)} -> {tmpStr}')
        return result
    except Exception as e:
        mylogger.error(f"something wrong happens: {e}")
        return ""