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
    # image_url = "https://oaidalleapiprodscus.blob.core.windows.net/private/org-TaVhM6pvPKbfl5EbylocW77I/user-0NnhYuR1inka90I7DroBShdd/img-zNmzfiBsK6kG9fddI1a2PCmT.png?st=2024-11-13T13%3A01%3A48Z&se=2024-11-13T15%3A01%3A48Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&skoid=d505667d-d6c1-4a0a-bac7-5c84a87759f8&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-11-12T19%3A51%3A15Z&ske=2024-11-13T19%3A51%3A15Z&sks=b&skv=2024-08-04&sig=BYJnowYfTXkKWyMtMuCffPLgOE/Fyev25CeqOFHqEIU%3D"

    # image_url = "https://oaidalleapiprodscus.blob.core.windows.net/private/org-TaVhM6pvPKbfl5EbylocW77I/user-0NnhYuR1inka90I7DroBShdd/img-CBc3cutshFIPNJTtQrgdmj1S.png?st=2024-11-13T13%3A17%3A56Z&se=2024-11-13T15%3A17%3A56Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&skoid=d505667d-d6c1-4a0a-bac7-5c84a87759f8&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-11-12T20%3A07%3A29Z&ske=2024-11-13T20%3A07%3A29Z&sks=b&skv=2024-08-04&sig=LYyHZc9fGjUcV6vKIMXjqBXVjAnbnkLpU5jM2PK80GQ%3D"
    
    print(f"Generated image URL: {image_url}")
    
    # Prepare and send the report
    answer = image_url

    # Send the report using the helper function
    result = send_report(answer, "robotid")
    print(f"Report submission result: {result}")
    
except Exception as e:
    print(f"Error during image generation or submission: {e}")
    raise
