import os
import requests

def send_report(answer, task_name):
    """Send report to Centrala with specified task name"""
    centrala_url = os.getenv('CENTRALA_URL')
    centrala_api_key = os.getenv('CENTRALA_API_KEY')
    
    # Debug environment variables
    print(f"Debug: CENTRALA_URL = {centrala_url}")
    print(f"Debug: CENTRALA_API_KEY = {centrala_api_key}")
    
    payload = {
        "task": task_name,
        "apikey": centrala_api_key,
        "answer": answer
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
