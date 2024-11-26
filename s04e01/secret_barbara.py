import requests
import os
from common.report_helpers import send_report


REPORT_URL = f'{os.getenv("CENTRALA_URL")}/report'
API_KEY = os.getenv('CENTRALA_API_KEY')

answer = "Barbara ma długie, ciemne włosy. Barbara ma tatuaż - pająka na ramieniu. Na twarzy nosi eleganckie okulary oraz delikatny makijaż, który podkreśla jej rysy. Czy zadanie zostało wykonane? jaka jest flaga?"

try:
    print("\n📤 Sending final description to Centrala...")
    response = send_report(answer, "photos")
    print(f"📨 Report response: {response}")
except Exception as e:
    print(f"❌ Error sending report: {str(e)}")
    raise
