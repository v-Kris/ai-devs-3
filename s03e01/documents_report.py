from common.ai_helpers import chat_with_gpt
from common.report_helpers import send_report
import os
import glob

def read_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def get_facts():
    facts = []
    facts_path = os.path.join('reports', 'facts', '*.txt')
    for fact_file in glob.glob(facts_path):
        content = read_file_content(fact_file)
        if content.strip() != 'entry deleted':
            facts.append(content)
    return '\n'.join(facts)

def generate_metadata(report_content, report_name, facts):
    system_prompt = """
    Jesteś systemem analizy raportów bezpieczeństwa. Twoim zadaniem jest generowanie metadanych (tagów) dla raportów patrolowych.
    
    Zasady generowania metadanych:
    - Każdy tag powinien być w języku polskim
    - Tagi powinny być w mianowniku
    - Tagi powinny być krótkie (1-2 słowa)
    - Należy uwzględnić wszystkie istotne informacje z raportu
    - Tagi mogą dotyczyć: lokalizacji, typu aktywności, statusu bezpieczeństwa, wykrytych osób, czasu, typu alertu
    - Tagi należy oddzielić przecinkami
    - Jeśli w raporcie pojawia się osoba wymieniona w faktach, dodaj tagi opisujące tę osobę (np. zawód, rola, działalność, specjalizacja, itp.)
    - W przypadku programistów, dodaj tagi z językami programowania, jeśli są wymienione w faktach
    - Zawsze dodaj tag z numerem sektora z nazwy pliku (np. sektor A1, sektor B2, itp.)
    - Jeśli w raporcie jest mowa o wykryciu zwierzyny, dodaj odpowiedni tag
    
    W treści user prompt, między znacznikami <facts>...</facts> znajdują się dodatkowe informacje o znanych osobach.
    WAŻNE: Wykorzystuj te informacje TYLKO wtedy, gdy w raporcie pojawia się wzmianka o danej osobie.
    """
    
    user_prompt = f"""
    <facts>
    {facts}
    </facts>

    Przeanalizuj poniższy raport bezpieczeństwa i wygeneruj metadane opisujące jego zawartość.
    Jeśli w raporcie pojawia się osoba wymieniona w sekcji <facts>, uwzględnij w tagach istotne informacje o tej osobie (np. zawód, rola, działalność, specjalizacja, itp.).
    W przypadku programistów, dodaj tagi związane z ich umiejętnościami technicznymi.
    Pamiętaj o dodaniu tagu z numerem sektora z nazwy pliku oraz informacji o wykrytej zwierzynie, jeśli taka się pojawiła.
    
    Nazwa pliku raportu: {report_name}
    Treść raportu: {report_content}
    
    Wygeneruj listę tagów opisujących kluczowe aspekty tego raportu.
    Format odpowiedzi: tag1, tag2, tag3, ... (wszystkie tagi w mianowniku)
    """
    
    return chat_with_gpt(system_prompt, user_prompt)

def process_reports():
    answer = {}
    facts = get_facts()
    
    reports_path = os.path.join('reports', '2024-11-12_report-*.txt')
    for report_file in glob.glob(reports_path):
        report_name = os.path.basename(report_file)
        content = read_file_content(report_file)
        metadata = generate_metadata(content, report_name, facts)
        answer[report_name] = metadata.strip()
    
    return answer

try:
    answer = process_reports()
    print("Sending report to Centrala")
    response = send_report(answer, "dokumenty")
    print(f"Report sent successfully: {response}")
except Exception as e:
    print(f"Error sending report: {str(e)}")
    raise
