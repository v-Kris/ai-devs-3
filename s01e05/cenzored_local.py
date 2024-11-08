import os
import requests
from common.local_llm_helper import get_ollama_answer

def get_text_from_centrala():
    centrala_url = os.getenv('CENTRALA_URL')
    centrala_api_key = os.getenv('CENTRALA_API_KEY')
    
    url = f"{centrala_url}/data/{centrala_api_key}/cenzura.txt"
    print(f"Debug: Fetching text from {url}")
    
    response = requests.get(url)
    response.raise_for_status()
    return response.text.strip()

def clean_text(text):
    """Clean text from extra whitespace and newlines"""
    # Remove extra whitespace and newlines
    cleaned = ' '.join(text.split())
    return cleaned.strip()

def cenzor_personal_data(text):
    text = clean_text(text)
    print(f"Debug: Original text (cleaned): {text}")
    
    prompt = f"""Replace the following personal information with a single word 'CENZURA'. Each replacement must be complete:

1. FULL names must be replaced entirely:
   - "Tomasz Zieliński" -> "CENZURA" (not "CENZURA Zieliński")
   - "Jan Kowalski" -> "CENZURA"

2. City names:
   - "w Poznaniu" -> "w CENZURA"
   - "Adres: Poznań" -> "Adres: CENZURA"

3. Complete street addresses (including number):
   - "ulica Piękna 5" -> "ulica CENZURA"
   - "ul. Konwaliowa 8" -> "ul. CENZURA"

4. Age numbers:
   - "25 lat" -> "CENZURA lat"
   - "24 lata" -> "CENZURA lata"

Important rules:
- Never leave parts of names visible
- Always include street numbers in CENZURA
- Each sensitive piece of information should be replaced with exactly one CENZURA

<examples>
USER: Podejrzany: Adam Nowak. Mieszka w Bydgoszczy przy ul. Sezamkowej 7. Ma 34 lata.
AI: Podejrzany: CENZURA. Mieszka w CENZURA przy ul. CENZURA. Ma CENZURA lata.

USER: Klient: Jan Kowalski. Mieszka w Warszawie przy ul. Czereśniowej 3. Ma 45 lat.
AI: Klient: CENZURA. Mieszka w CENZURA przy ul. CENZURA. Ma CENZURA lat.

USER: Klient: Jan Kowalski. Mieszka w Warszawie przy ul. Czereśniowej 3. Wiek 43 lata.
AI: Klient: CENZURA. Mieszka w CENZURA przy ul. CENZURA. Wiek CENZURA lata.
</examples>

Return only the modified text, with no additional explanations.

Original text: {text}"""
    
    # Get censored text directly from LLM
    censored_text = get_ollama_answer(prompt)
    
    # Clean output text
    censored_text = clean_text(censored_text)
    print(f"Debug: Cenzored text (cleaned): {censored_text}")
    return censored_text

def send_report(cenzored_text):
    centrala_url = os.getenv('CENTRALA_URL')
    centrala_api_key = os.getenv('CENTRALA_API_KEY')
    
    payload = {
        "task": "CENZURA",
        "apikey": centrala_api_key,
        "answer": cenzored_text
    }
    
    url = f"{centrala_url}/report"
    print(f"Debug: Sending report to {url}")
    print(f"Debug: Payload: {payload}")
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.text

def main():
    try:
        original_text = get_text_from_centrala()
        cenzored_text = cenzor_personal_data(original_text)
        response = send_report(cenzored_text)
        print(f"Debug: API Response: {response}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 
