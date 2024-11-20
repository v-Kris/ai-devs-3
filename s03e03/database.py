import requests
import os
from common.report_helpers import send_report
from common.ai_helpers import chat_with_gpt


DB_URL = f'{os.getenv("CENTRALA_URL")}/apidb'
API_KEY = os.getenv('CENTRALA_API_KEY')

def show_flag():
    response = requests.post(DB_URL, json={
        "task": "database",
        "apikey": API_KEY,
        "query": f"SELECT letter FROM correct_order ORDER BY weight"
    })
    
    flag = ''.join(item['letter'] for item in response.json()['reply'])

    print(flag)

def get_table_structure(table_name):
    response = requests.post(DB_URL, json={
        "task": "database",
        "apikey": API_KEY,
        "query": f"show create table {table_name}"
    })
    return response.json()

def get_active_unmanaged_datacenters():
    # Zdobądź strukturę tabel
    show_flag()
    users_structure = get_table_structure("users")
    datacenters_structure = get_table_structure("datacenters")
    # print(users_structure)
    # print(datacenters_structure)
    
    # Prepare system and user prompts for chat_with_gpt
    system_message = (
        "You are an SQL assistant tasked with returning only the SQL query result (in plain text, don't decorate it) "
        "Given the data structures below, return the IDs of all active datacenters "
        "whose managers (from the users table) are inactive.\n\n"
        "Table structures:\n"
        "Table: datacenters\n"
        f"{datacenters_structure}\n\n"
        "Table: users\n"
        f"{users_structure}\n"
    )
    
    user_message = (
        "Prepare an SQL query that returns the IDs of datacenters that are active, "
        "but their managers are inactive."
    )
    
    # Get SQL query from chat_with_gpt
    sql_query = chat_with_gpt(system_message, user_message)
    print(sql_query)
    
    # Wykonaj zapytanie
    response = requests.post(DB_URL, json={
        "task": "database",
        "apikey": API_KEY,
        "query": sql_query
    })
    
    return response.json()

# Wywołanie funkcji
active_datacenters = get_active_unmanaged_datacenters()
print(active_datacenters)

dc_ids = [item['dc_id'] for item in active_datacenters['reply']]

print(dc_ids)

try:
    print("Sending report to Centrala")
    response = send_report(dc_ids, "database")
    print(f"Report sent successfully: {response}")
except Exception as e:
    print(f"Error sending report: {str(e)}")
    raise
