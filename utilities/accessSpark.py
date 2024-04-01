from utilities import SparkApi
from utilities import logger
mylogger = logger.Logger(name=logger.SEARCHALL_LOG_FILE_NAME, debug=True).logger

#以下密钥信息从控制台获取
appid = "36fd7805"     #填写控制台中获取的 APPID 信息
api_secret = "ZDYzMmZlYzFiNTM3ODJmMGRlMzY2NzFi"   #填写控制台中获取的 APISecret 信息
api_key ="d46dd60999c2143a71693ef15c025c9c"    #填写控制台中获取的 APIKey 信息

#用于配置大模型版本，默认“general/generalv2”
#domain = "general"   # v1.5版本
domain = "generalv3"    # v2.0版本
#云端环境的服务地址
# Spark_url = "ws://spark-api.xf-yun.com/v1.1/chat"  # v1.5环境的地址
# Spark_url = "ws://spark-api.xf-yun.com/v2.1/chat"  # v2.0环境的地址
Spark_url = "ws://spark-api.xf-yun.com/v3.5/chat" 


text =[]

# length = 0

def getText(role,content):
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = content
    text.append(jsoncon)
    return text

def getlength(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length

def checklen(text):
    while (getlength(text) > 8000):
        del text[0]
    return text
    

def get_feedback_Spark(system_string, code):
    messages = []
    jsoncon = {}
    # jsoncon["role"] = 'system'
    # jsoncon["content"] = system_string
    # messages.append(jsoncon)

    jsoncon['role'] = 'user'
    jsoncon['content'] =  system_string + "\n代码如下:\n" + code
    messages.append(jsoncon)
    SparkApi.answer =""
    mylogger.debug('------------------ Start to query Spark 3.5....')
    SparkApi.main(appid,api_key,api_secret,Spark_url,domain,messages)
    tmpStr = SparkApi.answer[:50].replace('\n', ' ')
    mylogger.debug(f'Get answer {len(SparkApi.answer)} -> {tmpStr}')

    return SparkApi.answer


if __name__ == '__main__':
    import os
    os.chdir('c:/repo/nstc-copilot')
    text.clear
    res = get_feedback_Spark('please answer in Chinese', '你好')
    print(f'\nThis is the feedback: {res}')


    while(1):
        Input = input("\n" +"我:")
        question = checklen(getText("user",Input))
        SparkApi.answer =""
        print("星火: wait for answer...",end = "")
        SparkApi.main(appid,api_key,api_secret,Spark_url,domain,question)
        print("\nComplete loop")
        getText("assistant",SparkApi.answer)
        # print(str(text))

