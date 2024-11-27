import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from langfuse.openai import OpenAI
from common.report_helpers import send_report
import json

# Initialize Langfuse OpenAI client
client = OpenAI()

def analyze_page_content(content, question):
    """Analizuje zawartość strony pod kątem odpowiedzi na pytanie."""
    system_prompt = """Jesteś asystentem analizującym zawartość stron internetowych.
    Twoim zadaniem jest:
    1. Określić, czy strona zawiera odpowiedź na pytanie w przekazanym tekście
    2. Jeśli tak - wyodrębnić odpowiedź
    3. Jeśli nie - przeanalizować dostępne linki i zaproponować listę najbardziej obiecujących linków do eksploracji
    
    Otrzymasz słownik zawierający:
    - "text": treść strony
    - "links": listę dostępnych linków, gdzie każdy link ma "href" (URL) i "text" (tekst wyświetlany)
    
    Odpowiedz TYLKO w formacie: 
    {"contains_answer": bool, "answer": str|null, "next_links": [str]|null}
    
    Dla next_links użyj dokładnych wartości href z listy dostępnych linków."""

    user_prompt = f"""Pytanie: {question}
    Zawartość strony: {content}
    
    Czy ta strona zawiera odpowiedź na pytanie? Jeśli tak, podaj odpowiedź.
    Jeśli nie, wskaż który link wygląda najbardziej obiecująco (jeśli są)."""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    try:
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ Błąd podczas analizy LLM: {e}")
        return None

def search_softoai():
    base_url = "https://softo.ag3nts.org"
    visited_links = set()
    answers = {}

    def visit_page(url, question_number, question):
        if url in visited_links:
            print(f"🔄 Pomijam już odwiedzony URL: {url}")
            return None
        
        print(f"\n🌐 Odwiedzam stronę: {url}")
        visited_links.add(url)

        try:
            page = requests.get(url)
            page.raise_for_status()
            soup = BeautifulSoup(page.content, 'html.parser')
            print(f"✅ Pobrano stronę: {url}")

            links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                text = link.get_text(strip=True)
                links.append({"href": href, "text": text})

            content = {
                "text": soup.get_text(separator=' ', strip=True),
                "links": links
            }
            
            analysis = analyze_page_content(content, question)
            
            if analysis:
                try:
                    result = json.loads(analysis)
                    
                    if result.get("contains_answer"):
                        answers[question_number] = result["answer"]
                        print(f"💡 Znaleziono odpowiedź na pytanie {question_number}: {result['answer']}")
                        return True
                    elif result.get("next_links"):
                        for next_url in result["next_links"]:
                            if next_url not in visited_links:
                                if not next_url.startswith('http'):
                                    next_url = urljoin(base_url, next_url)
                                print(f"🔍 Próbuję link: {next_url}")
                                if visit_page(next_url, question_number, question):
                                    return True
                        
                        print("❌ Żaden z sugerowanych linków nie zawierał odpowiedzi")
                        return False
                except json.JSONDecodeError as e:
                    print(f"❌ Błąd podczas parsowania JSON: {e}")
                    return False
            
            print(f"❌ Nie znaleziono odpowiedzi na tej stronie")
            return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Błąd podczas pobierania strony {url}: {e}")
            return False

    # Pobierz pytania
    try:
        api_key = os.getenv('CENTRALA_API_KEY')
        questions_url = f"https://centrala.ag3nts.org/data/{api_key}/softo.json"
        response = requests.get(questions_url)
        questions = response.json()
        print(f"📝 Pobrano pytania: {questions}")
    except Exception as e:
        print(f"❌ Błąd podczas pobierania pytań: {e}")
        return {}

    # Przeszukaj stronę dla każdego pytania
    for question_number, question in questions.items():
        print(f"\n📋 Rozpoczynam szukanie odpowiedzi na pytanie {question_number}: {question}")
        
        # Reset visited links for each question
        visited_links = set()
        
        # Start searching from the base URL
        visit_page(base_url, question_number, question)

    return answers

if __name__ == "__main__":
    print("\n🚀 Rozpoczynam przeszukiwanie strony SoftoAI...")
    answers = search_softoai()
    print(f"📤 Wysyłana odpowiedź: {answers}")

    try:
        response = send_report(answers, "softo")
        print(f"📨 Report response: {response}")
    except Exception as e:
        print(f"❌ Error sending report: {str(e)}")
        raise