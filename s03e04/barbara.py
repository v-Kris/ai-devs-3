import json
import os
import requests
from langfuse.openai import OpenAI

client = OpenAI()

INIT_TXT = f'{os.getenv("CENTRALA_URL")}/dane/barbara.txt'
PEOPLE_URL = f'{os.getenv("CENTRALA_URL")}/people'
PLACES_URL = f'{os.getenv("CENTRALA_URL")}/places'
API_KEY = os.getenv('CENTRALA_API_KEY')

def get_initial_txt():
    response = requests.get(INIT_TXT)
    return response.text

def ask_people(items_list: list):
    unique_places = set()
    for name in items_list:
        response = requests.post(PEOPLE_URL, json={
            "apikey": API_KEY,
            "query": name
        })
        print(response.text)
        
        if response.status_code == 200:
            places_string = response.json().get('message', '')
            if '[**RESTRICTED DATA**]' in places_string:
                continue
            places = [place.strip() for place in places_string.split() if place.strip()]
            unique_places.update(places)
        else:
            print(f"Error fetching data for {name}: {response.status_code}")

    places_list = list(unique_places)
    print(places_list)
    return places_list

def ask_places(items_list: list):
    unique_names = set()
    for place in items_list:
        response = requests.post(PLACES_URL, json={
            "apikey": API_KEY,
            "query": place
        })
        print(response.text)
        
        if response.status_code == 200:
            names_string = response.json().get('message', '')
            if '[**RESTRICTED DATA**]' in names_string:
                continue
            names = [p.strip() for p in names_string.split() if p.strip()]
            unique_names.update(names)
        else:
            print(f"Error fetching data for {place}: {response.status_code}")

    names_list = list(unique_names)
    print(names_list)
    return names_list

def find_barbara_flag():
    # Initial lists
    people_list = ['Barbara', 'Aleksander', 'Andrzej', 'Rafal']
    places_list = ['Warszawa', 'Krakow']
    
    # Prepare initial messages
    messages = [
        {
            "role": "system", 
            "content": '''You are a helpful assistant to find single location of Barbara. 
Use call functions in tools to capture info about people and places to get final answer of Barbara location. 
IMPORTANT RULES:
1. DO NOT USE ANY PREVIOUSLY TESTED VALUES AS ARGUMENTS IN YOUR FUNCTION CALLS
2. Keep track of all values that have been previously tested
3. Only use NEW values not seen in previous iterations
4. Final answer should be as flag_name in format like {{FLG:<flag_name>}}

If you cannot find new values to test, explain why and attempt to derive new potential search values creatively.'''
        },
        {
            "role": "user", 
            "content": f'Here are initial places: "{places_list}" and people: "{people_list}" to check in functions what you get answers. When you get answers, please DO NOT USE POLISH LETTERS in any passed arguments.'
        }
    ]
    
    # Tools definition
    tools = [
        {
            "type": "function",
            "function": {
                "name": "ask_people",
                "description": "Function to check people's places when getting a list of people names.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "items_list": {
                            "type": "array",
                            "description": "List of peoples names",
                            "items": {
                                "type": "string"
                            },
                        },
                    },
                    "required": ["items_list"],
                    "additionalProperties": False,
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "ask_places",
                "description": "Function to check people's name when getting a list of places.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "items_list": {
                            "type": "array",
                            "description": "List of places names",
                            "items": {
                                "type": "string"
                            },
                        },
                    },
                    "required": ["items_list"],
                    "additionalProperties": False,
                },
            }
        }
    ]
    
    # Available functions
    available_functions = {
        "ask_people": ask_people,
        "ask_places": ask_places,
    }
    
    # Maximum iterations to prevent infinite loop
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        # Create chat completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        # Check if response contains the flag
        if response_message.content and '{{FLG:' in response_message.content:
            print("Flag found:", response_message.content)
            return response_message.content
        
        # If no tool calls, break the loop
        if not tool_calls:
            print("No more tool calls possible")
            break
        
        # Add response message to messages
        messages.append(response_message)
        
        # Process tool calls
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            
            # Call the function
            function_response = function_to_call(items_list=function_args.get("items_list"))
            
            # Add tool response to messages
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": ", ".join(function_response),
                }
            )
        
        iteration += 1
    
    print("Max iterations reached or flag not found")
    return None

# Run the flag finder
result = find_barbara_flag()
print("Final result:", result)
