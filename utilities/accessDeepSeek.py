from openai import OpenAI
from utilities import logger
import os
#os.environ['OPENAI_API_KEY'] = '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'
API_KEY = 'sk-48bdb88094644d8eaf176a0c203811e4'
mylogger = logger.Logger(name='copilot', debug=True).logger 
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com/v1")

def get_feedback_Deepseek(system_string, code):    
    mylogger.debug('------------------ Start to query Deepseek Coder....')
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role":"system", "content":system_string},
                    {"role":"user","content":code}],
        temperature=1,
        max_tokens=4095,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0)

    #mylogger.debug(response)
    answer = response.choices[0].message.content
    tmpStr = answer[:50].replace('\n', '  ')
    mylogger.debug(f'Get answer {len(answer)} -> {tmpStr}')
    return answer