import json
import os
import requests
from common.report_helpers import send_report
from neo4j import GraphDatabase


DB_URL = f'{os.getenv("CENTRALA_URL")}/apidb'
API_KEY = os.getenv('CENTRALA_API_KEY')

def get_users():
    response = requests.post(DB_URL, json={
        "task": "database",
        "apikey": API_KEY,
        "query": "SELECT * FROM users"
    })
    return response.json().get('reply')

def get_connections():
    response = requests.post(DB_URL, json={
        "task": "database",
        "apikey": API_KEY,
        "query": "SELECT * FROM connections"
    })
    return response.json().get('reply')


users = get_users()
connections = get_connections()

print(users)
print(connections)


URI = os.getenv('NEO4J_URI')
AUTH = (os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    try:
        for user in users:
            records, summary, keys = driver.execute_query(
                "MERGE (u:User {name: $username, user_id: $user_id})",
                username=user['username'],
                user_id=user['id'],
                database_="neo4j",
            )
        
            for connection in connections:
                records, summary, keys = driver.execute_query('''
                    MATCH (u1:User {user_id: $user1_id})
                    MATCH (u2:User {user_id: $user2_id})
                    MERGE (u1)-[:KNOWS]->(u2)
                    ''',
                    user1_id=connection['user1_id'],
                    user2_id=connection['user2_id'],
                    database_="neo4j",
                )
        records, summary, keys  = driver.execute_query(
                '''
                MATCH (start:User {name: 'Rafał'}), (end:User {name: 'Barbara'})
                MATCH p = shortestPath((start)-[:KNOWS*]-(end))
                RETURN [n in nodes(p) | n.name] AS path
                '''
            )
        
        print(records)
        print(summary)
        print(keys)

        for record in records:
            path_str = ', '.join(record['path'])
            print(path_str)

    except Exception as e:
        print(e)

try:
    print("Sending report to Centrala")
    response = send_report(path_str, "connections")
    print(f"Report sent successfully: {response}")
except Exception as e:
    print(f"Error sending report: {str(e)}")
    raise
