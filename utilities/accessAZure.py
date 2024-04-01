#Note: The openai-python library support for Azure OpenAI is in preview.
import os
from openai import AzureOpenAI
from utilities import logger
mylogger = logger.Logger(name='copilot', debug=True).logger

os.environ['AZURE_OPENAI_API_KEY'] = '8a893aed015240fbbbec78484efc0446'


def get_feedback_AZure(system_string, code, history=None):
    messages = [{'role':'system', 'content':system_string}]
    if history is not None:
        messages.extend(history)
    messages.append({'role':'user', 'content': code})

    client = AzureOpenAI(
        # https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#rest-api-versioning
        api_version="2024-02-15-preview",
        # https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal#create-a-resource
        azure_endpoint="https://llmchat.openai.azure.com/",
    )
    mylogger.debug('------------------ Start to query GPT 3.5 via Azure....')
    response = client.chat.completions.create(
        model="checkGPT35_16K",
        messages = messages,
        temperature=0.9,
        max_tokens=6000,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)

    text = response.choices[0].message.content
    tmpStr = text[:50].replace('\n', '  ')
    mylogger.debug(f'Get answer {len(text)} -> {tmpStr}')
    
    return text