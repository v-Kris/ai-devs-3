import re
import requests
from bs4 import BeautifulSoup
import json
import os

LOGIN_URL = 'http://xyz.ag3nts.org'
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
API_URL = os.getenv("API_URL")
LLM_API_URL = os.getenv("LLM_API_URL")
api_key = os.getenv("API_KEY")

def get_answer_from_llm(question: str) -> str:
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    data = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'system', 'content': 'Odpowiadaj jedną liczbą'},
            {'role': 'user', 'content': question},
        ],
        'max_tokens': 50
    }
    response = requests.post(LLM_API_URL, headers=headers, data=json.dumps(data))
    response_data = response.json()
    print(response_data)
    return response_data['choices'][0]['message']['content'].strip()

def get_current_question() -> str:
    response = requests.get(LOGIN_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    question = soup.find(id='human-question')
    if not question:
        raise ValueError('Nie udało się znaleźć pytania.')
    return question.text.strip()

def login_and_get_secret_page():
    try:
        question = get_current_question()
        print('Pobrane pytanie:', question)
        answer = get_answer_from_llm(question)
        print('Odpowiedź LLM:', answer)
        login_data = {
            'username': USERNAME,
            'password': PASSWORD,
            'answer': answer
        }
        login_response = requests.post(LOGIN_URL, data=login_data)
        result_text = login_response.content.decode("utf8")
        print("\nThe result page is:\n")
        print(result_text)
        flag = re.findall("{{FLG:(.*?)}}", result_text)
        if flag:
            print(f"\n\nZnaleziono flagę: {flag[0]}")
    except Exception as e:
        print('Wystąpił błąd:', e)

login_and_get_secret_page()
