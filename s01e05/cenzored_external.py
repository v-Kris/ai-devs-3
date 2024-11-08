import os
import requests
from common.ai_helpers import get_openai_answer

def get_text_from_centrala():
    centrala_url = os.getenv('CENTRALA_URL')
    centrala_api_key = os.getenv('CENTRALA_API_KEY')
    
    url = f"{centrala_url}/data/{centrala_api_key}/cenzura.txt"
    print(f"Debug: Fetching text from {url}")
    
    response = requests.get(url)
    response.raise_for_status()
    return response.text.strip()

def cenzor_personal_data(text):
    print(f"Debug: Original text: {text}")
    
    prompt = f"""Analyze this text and find ONLY the following items (return each found item in new line):
1. Full name (first and last name)
2. City name without preposition (e.g., from 'w Poznaniu' return only 'Poznaniu')
3. Street name and number without prefix (e.g., from 'ulica Konwaliowa 18' return only 'Konwaliowa 18')
4. Age number only (without word 'lat')

Text to analyze: {text}"""
    
    # Get all sensitive information at once
    answer = get_openai_answer(prompt)
    if answer:
        # Split the answer into lines and process each found item
        for item in answer.strip().split('\n'):
            if item:
                text = text.replace(item.strip(), "CENZURA")
    
    print(f"Debug: Cenzored text: {text}")
    return text

def send_report(cenzored_text):
    centrala_url = os.getenv('CENTRALA_URL')
    centrala_api_key = os.getenv('CENTRALA_API_KEY')
    
    # Debug environment variables
    print(f"Debug: CENTRALA_URL = {centrala_url}")
    print(f"Debug: CENTRALA_API_KEY = {centrala_api_key}")
    
    payload = {
        "task": "CENZURA",
        "apikey": centrala_api_key,
        "answer": cenzored_text
    }
    
    url = f"{centrala_url}/report"
    print(f"Debug: Full URL = {url}")
    print(f"Debug: Request payload = {payload}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"Debug: Response status code = {response.status_code}")
        print(f"Debug: Response headers = {dict(response.headers)}")
        print(f"Debug: Response content = {response.text}")
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Debug: Request failed with error: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Debug: Error response content: {e.response.text}")
        raise

def main():
    try:
        # Get text from Centrala
        original_text = get_text_from_centrala()
        
        # Cenzor personal data
        cenzored_text = cenzor_personal_data(original_text)
        
        # Send report
        response = send_report(cenzored_text)
        print(f"Debug: API Response: {response}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 
