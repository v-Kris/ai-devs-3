import os
import requests
from openai import OpenAI

# Function to calculate the answer from a math question
def calculate_answer(question):
    try:
        # Evaluate the mathematical expression in the question
        answer = eval(question)
        return answer
    except Exception as e:
        print(f"Error calculating answer for question '{question}': {e}")
        return None  # Return None if there's an error

# Function to get the answer to a question using OpenAI
def get_openai_answer(question):
    try:
        client = OpenAI()

        print(f"Debug: Generating answer for question: '{question}'")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Specify the model you want to use
            messages=[
                {"role": "system", "content": "Please provide a single-word answer."},  # System message
                {"role": "user", "content": question}
            ]
        )
        
        # Extract the answer from the response
        answer = response.choices[0].message.content.strip()
        print(f"Debug: OpenAI response: '{answer}'")
        return answer
    except Exception as e:
        print(f"Error getting answer from OpenAI for question '{question}': {e}")
        raise

# Get environment variables
centrala_url = os.getenv('CENTRALA_URL')
centrala_api_key = os.getenv('CENTRALA_API_KEY')

# Debugging: Print the retrieved environment variables
print(f"CENTRALA_URL: {centrala_url}")
print(f"CENTRALA_API_KEY: {centrala_api_key}")

# Construct the full URL to get the JSON file
json_url = f"{centrala_url}/data/{centrala_api_key}/json.txt"
print(f"Constructed JSON URL: {json_url}")

# Fetch the JSON data
response = requests.get(json_url)
print(f"HTTP Response Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("Successfully fetched JSON data.")
else:
    raise Exception(f"Failed to fetch data: {response.status_code}")

# Update the JSON fields
data['apikey'] = centrala_api_key
print(f"Updated apikey in JSON data: {data['apikey']}")

# Iterate through "test-data" and check answers
for item in data['test-data']:
    question = item['question']
    expected_answer = item['answer']
    
    # Debugging: Print the question and expected answer
    print(f"Question: {question}, Expected Answer: {expected_answer}")
    
    # Calculate the correct answer for the math question
    correct_answer = calculate_answer(question)
    
    # Debugging: Print the calculated answer
    print(f"Calculated Answer: {correct_answer}")
    
    # Update the answer in the JSON
    item['answer'] = correct_answer

    # Check if there is a test question and get the answer using OpenAI
    if 'test' in item:
        test_question = item['test']['q']
        openai_answer = get_openai_answer(test_question)
        
        # Update the test answer in the JSON
        item['test']['a'] = openai_answer
        print(f"Updated test answer for '{test_question}': {openai_answer}")

# Prepare the body for the POST request
post_body = {
    "task": "JSON",
    "apikey": centrala_api_key,
    "answer": data  # The updated JSON with correct answers
}

# Send the updated JSON as a POST request
post_url = f"{centrala_url}/report"
post_response = requests.post(post_url, json=post_body)

# Debugging: Print the response from the POST request
print(f"POST Response Status Code: {post_response.status_code}")
print(f"POST Response Body: {post_response.json() if post_response.status_code == 200 else post_response.text}")

# ... existing code ...

