import requests

def create_embedding_bge(sentence):
    response = requests.post('http://10.101.9.50:5111/genvec', json={'question': sentence})
    return response.json()