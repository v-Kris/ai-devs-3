import os
import requests
from openai import OpenAI


API_URL = os.getenv("API_URL")
session = requests.Session()

def send_ready():
    response = session.post(API_URL, json={"text": "READY", "msgID": 0})
    response_data = response.json()
    print(f"Debug: Sent 'READY', received response: {response_data}")
    return response_data

def send_answer(msgID, answer):
    response = session.post(API_URL, json={"text": answer, "msgID": msgID})
    response_data = response.json()
    print(f"Debug: Sent answer '{answer}' for msgID '{msgID}', received response: {response_data}")
    return response_data

def generate_single_word_answer(question):
    client = OpenAI()

    print(f"Debug: Generating answer for question: '{question}'")
    response = client.chat.completions.create(
        messages=[
            {
                'role': 'system',
                'content': 'Give answer in English language for single question included in whole text using just '
                           'single word without any marks, dots, etc. There are 3 questions for that the answer must '
                           'be wrong: 1. question is for capital of Poland - answer Kraków, 2. The Hitchhikers '
                           'Guide book - answer 69, 3. question is regarding actual year now - answer 1999',
            },
            {
                'role': 'user',
                'content': question
            },
        ],
        model='gpt-3.5-turbo',
        max_tokens=20,
        temperature=0,
    )

    answer = response.choices[0].message.content.strip()
    print(f"Debug: OpenAI response: '{answer}'")
    return answer

def process_verification():
    response = send_ready()
    
    question = response["text"]
    msgID = response["msgID"]
    
    answer = generate_single_word_answer(question)
    
    response = send_answer(msgID, answer)

process_verification()
