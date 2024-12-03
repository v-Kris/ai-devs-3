import os
import requests
import json
from langfuse.openai import OpenAI
from typing import Dict, Any, List
import time
from common.report_helpers import send_report

# Configuration
DB_URL = f'{os.getenv("CENTRALA_URL")}/apidb'
PLACES_URL = f'{os.getenv("CENTRALA_URL")}/places'
GPS_URL = f'{os.getenv("CENTRALA_URL")}/gps'
API_KEY = os.getenv('CENTRALA_API_KEY')
REPORT_URL = f'{os.getenv("CENTRALA_URL")}/report'
INITIAL_QUESTION = f'{os.getenv("CENTRALA_URL")}/data/{API_KEY}/gps_question.json'


# Initialize OpenAI client
client = OpenAI()

class GPSAgent:
    def __init__(self):
        self.tools = {
            "database": self._query_database,
            "places": self._query_places,
            "gps": self._query_gps
        }
    
    def get_initial_question(self) -> str:
        print("> Reading data from file...")
        try:
            response = requests.get(INITIAL_QUESTION)
            data = response.json()
            print("> Reading data from file... [OK]")
            return data.get("question", "")
        except json.JSONDecodeError:
            print("  - FATAL: Error reading file - this is not a valid JSON")
            raise
        except Exception as e:
            print(f"  - FATAL: Error reading file - {str(e)}")
            raise

    def process_query(self, query: str = None) -> Dict[str, Any]:
        print("> Starting Agent... [OK]")
        
        if query is None:
            query = self.get_initial_question()
        
        print("> Processing user question... [OK]")
        print("> Preparing plan...")
        
        # Use GPT-4o-mini with updated system prompt
        analysis = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": """You are a query analyzer. Your task is to determine if the input is a username or a place name.
                For usernames, retain Polish characters. For place names, convert to uppercase and remove Polish characters.
                If there's any mention of prohibited or excluded places/users:
                - For prohibited places: convert to uppercase and remove Polish characters
                - For prohibited users: convert to uppercase and remove Polish characters
                
                Respond in the following JSON format only without markdown formatting:
                {
                    "type": "username" or "place",
                    "value": "extracted value",
                    "confidence": 0-1 score,
                    "prohibited_places": ["UPPERCASE", "WITHOUT", "POLISH", "CHARS"] or [],
                    "prohibited_users": ["UPPERCASE", "WITHOUT", "POLISH", "CHARS"] or []
                }
                Do not include any additional explanation."""
            }, {
                "role": "user",
                "content": query
            }]
        )
        
        try:
            analysis_result = json.loads(analysis.choices[0].message.content)
            query_type = analysis_result["type"]
            query_value = analysis_result["value"]
            prohibited_places = analysis_result.get("prohibited_places", [])
            prohibited_users = analysis_result.get("prohibited_users", [])
            
            print(f"  - Step 1: Check if this is username or place - select API or DB [OK]")
            
            if prohibited_places:
                print(f"     - INFO: Found prohibited places: {prohibited_places}")
            if prohibited_users:
                print(f"     - INFO: Found prohibited users: {prohibited_users}")
            
            if query_type == "username":
                return self._handle_username_flow(query_value, prohibited_users)
            else:
                return self._handle_place_flow(query_value, prohibited_places, prohibited_users)
                
        except json.JSONDecodeError:
            print("> FATAL: Could not parse LLM response")
            print("> Sending debug information to developers... [OK]")
            return {"error": "Invalid LLM response format"}
        except Exception as e:
            print(f"> FATAL: {str(e)}")
            print("> Sending debug information to developers... [OK]")
            return {"error": str(e)}

    def _handle_username_flow(self, username: str, prohibited_users: List[str] = None) -> Dict[str, Any]:
        if prohibited_users and username.upper() in prohibited_users:
            print(f"     - INFO: Skipping prohibited user '{username}'")
            return {"error": "Prohibited user"}
            
        print(f"     - INFO: username found - '{username}'")
        
        # Check database for user
        user_id = self._query_database(f"SELECT id FROM users WHERE username = '{username}'")
        print(f"  - Step 2: Check if user exists in external MySQL database... [OK]")
        print(f"     - INFO: user found - '{username}' with ID={user_id}")
        
        # Get GPS coordinates
        print("  - Step 3: Get user GPS coordinates from external API...")
        return self._query_gps(user_id)

    def _handle_place_flow(self, place: str, prohibited_places: List[str] = None, prohibited_users: List[str] = None) -> Dict[str, Any]:
        if prohibited_places and place in prohibited_places:
            print(f"     - INFO: Skipping prohibited place '{place}'")
            return {"error": "Prohibited place"}
            
        print(f"     - INFO: place found - '{place}'")
        
        # Check if place exists in external API
        place_info = self._query_places(place)
        print(place_info)
        
        # Check if place exists based on code
        if place_info.get('code') != 0:
            print("     - INFO: not found. Skipping...")
            return {"error": "Place not found"}
        
        # Extract users from the message string
        users = place_info.get('message', '').split()
        print("  - Step 4: Extracting users from that place... [OK]")
        
        print("  - Step 5: Checking users in database [OK]")
        valid_users = []
        for user in users:
            # Skip prohibited users
            if prohibited_users and user.upper() in prohibited_users:
                print(f"     - Skipping prohibited user '{user}'")
                continue
                
            user_id = self._query_database(f"SELECT id FROM users WHERE username = '{user}'")
            if user_id:
                valid_users.append((user, user_id))
            else:
                print(f"     - Skipping user '{user}' - doesn't exist")
        
        print("  - Step 6: Getting GPS coordinates for users... [OK]")
        final_data = {}
        for user, user_id in valid_users:
            try:
                gps_response = self._query_gps(user_id)
                if gps_response.get('code') == 0:
                    coords = gps_response.get('message', {})
                    final_data[user.lower()] = {
                        "lat": coords.get("lat"),
                        "lon": coords.get("lon")
                    }
                    print(f"     - got: {coords}")
            except Exception as e:
                print(f"     - Error for user '{user}': {str(e)}")
        
        print("  - Step 8: Preparing final data...")
        print(f"     - JSON created [OK]")
        print(f"     - sending data to {REPORT_URL} as 'gps'")
        
        try:
            print("Sending report to Centrala")
            response = send_report(final_data, "gps")
            print(f"Report sent successfully: {response}")
        except Exception as e:
            print(f"Error sending report: {str(e)}")
            raise
        
        print("  - Step 9: Checking confirmation from centrala...")
        if response.status_code == 200:
            print("     - returned code: 0")
            print("     - returned message: 'Answer accepted'")
        else:
            print(f"     - returned code: {response.status_code}")
            print(f"     - returned message: {response.text}")
        
        return final_data

    def _query_database(self, query: str) -> Any:
        response = requests.post(DB_URL, json={
            "task": "database",
            "apikey": API_KEY,
            "query": query
        })
        
        data = response.json()
        # Check if we have a valid response with results
        if data.get('error') == 'OK' and data.get('reply'):
            # Extract the ID from the first result
            return data['reply'][0].get('id')
        return None

    def _query_places(self, place: str) -> Dict[str, Any]:
        response = requests.post(PLACES_URL, json={
            "apikey": API_KEY,
            "query": place
        })
        return response.json()

    def _query_gps(self, user_id: str, max_retries: int = 3) -> Dict[str, Any]:
        print("     - preparing JSON for the request")
        print("     - sending request to /gps")
        
        for attempt in range(max_retries):
            try:
                response = requests.post(GPS_URL, json={
                    "apikey": API_KEY,
                    "userID": user_id
                })
                return response.json()
            except Exception as e:
                if attempt < max_retries - 1:
                    print("       - Retrying...")
                    time.sleep(1)
                else:
                    raise e

# Usage
if __name__ == "__main__":
    agent = GPSAgent()
    result = agent.process_query()
    print(result)
