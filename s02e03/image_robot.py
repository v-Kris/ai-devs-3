import os
import requests
from langfuse.openai import OpenAI
from common.report_helpers import send_report

# Get environment variables
centrala_url = os.getenv('CENTRALA_URL')
centrala_api_key = os.getenv('CENTRALA_API_KEY')

# Construct the URL for the robot description
json_url = f"{centrala_url}/data/{centrala_api_key}/robotid.json"
print(f"Fetching robot description from: {json_url}")

# Fetch the JSON data
response = requests.get(json_url)
if response.status_code != 200:
    raise Exception(f"Failed to fetch robot description: {response.status_code}")

# Parse the JSON response
data = response.json()
robot_description = data.get('description')
print(f"Retrieved robot description: {robot_description}")

# Initialize OpenAI client
client = OpenAI()

# Generate image using DALL-E 3
try:
    print("Generating robot image with DALL-E 3...")
    response = client.images.generate(
        model="dall-e-3",
        prompt=robot_description,
        size="1024x1024",
        quality="standard",
        n=1,
        response_format="url"
    )

    
    # Get the image URL from the response
    image_url = response.data[0].url

    print(f"Generated image URL: {image_url}")
    
    # Prepare and send the report
    answer = image_url

    # Send the report using the helper function
    result = send_report(answer, "robotid")
    print(f"Report submission result: {result}")
    
except Exception as e:
    print(f"Error during image generation or submission: {e}")
    raise
