import os
from common.report_helpers import send_report
from flask import Flask, request, jsonify
from langfuse.openai import OpenAI

app = Flask(__name__)
llm = OpenAI()

REPORT_URL = f'{os.getenv("CENTRALA_URL")}'
API_KEY = os.getenv('CENTRALA_API_KEY')

MAP = {
    (0, 3): "start",
    (1, 3): "trawa",
    (2, 3): "drzewo",
    (3, 3): "dom",

    (0, 2): "trawa",
    (1, 2): "wiatrak",
    (2, 2): "trawa",
    (3, 2): "trawa",

    (0, 1): "trawa",
    (1, 1): "trawa",
    (2, 1): "skały",
    (3, 1): "drzewa",

    (0, 0): "góry",
    (1, 0): "góry",
    (2, 0): "samochód",
    (3, 0): "jaskinia"
}

SYSTEM_PROMPT = """
Jesteś precyzyjnym nawigatorem drona na mapie 4x4. Mapa ma następujące właściwości:
- Współrzędne x rosną od lewej (0) do prawej (3)
- Współrzędne y maleją od góry (3) do dołu (0)
- Start jest zawsze w punkcie (0,3) - lewy górny róg
- Każdy ruch "w prawo" zwiększa x o 1
- Każdy ruch "w lewo" zmniejsza x o 1
- Każdy ruch "w dół" zmniejsza y o 1
- Każdy ruch "w górę" zwiększa y o 1

Mapa:
(0,3): start, (1,3): trawa, (2,3): drzewo, (3,3): dom
(0,2): trawa, (1,2): wiatrak, (2,2): trawa, (3,2): trawa
(0,1): trawa, (1,1): trawa, (2,1): skały, (3,1): drzewa
(0,0): góry, (1,0): góry, (2,0): samochód, (3,0): jaskinia

Twoim zadaniem jest przeanalizować instrukcję w języku naturalnym i zwrócić końcowe współrzędne (x,y).
Pamiętaj:
- Dron nie może wyjść poza mapę (x: 0-3, y: 0-3)
- Zawsze zaczynamy od punktu (0,3)
- Jeśli instrukcja prowadzi poza mapę, zatrzymaj się na ostatniej możliwej pozycji

Zwróć tylko parę liczb x,y, np.: "2,1"
"""

def parse_ai_coordinates(instruction: str) -> tuple[int, int]:
    """Use AI to parse instruction and return coordinates"""
    prompt = f"Instrukcja: {instruction}\nPodaj współrzędne końcowe w formacie 'x,y':"
    
    response = llm.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Debugging: print model's response
    print(f"<thinking> Model response: {response.choices[0].message.content.strip()} </thinking>")
    
    try:
        x, y = map(int, response.choices[0].message.content.strip().split(','))
        # Ensure coordinates are within bounds
        x = max(0, min(3, x))
        y = max(0, min(3, y))
        return (x, y)
    except:
        return (0, 3)  # Return to start if parsing fails

@app.route("/", methods=["POST"])
def handle_drone():
    data = request.get_json()
    
    if not data or "instruction" not in data:
        return jsonify({"error": "Missing instruction"}), 400
        
    coords = parse_ai_coordinates(data["instruction"])
    description = MAP.get(coords, "nieznane")
    
    return jsonify({"description": description})

if __name__ == "__main__":
    # answer = "<https://azyl-50215.ag3nts.org/api>"

    # try:
    #     print("\n📤 Sending final description to Centrala...")
    #     response = send_report(answer, "webhook")
    #     print(f"📨 Report response: {response}")
    # except Exception as e:
    #     print(f"❌ Error sending report: {str(e)}")
    #     raise

    app.run(host="0.0.0.0", port=8000)
