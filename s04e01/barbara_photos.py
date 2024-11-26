import requests
import os
import base64
from io import BytesIO
from openai import OpenAI
from langfuse.openai import OpenAI as LangfuseOpenAI
from common.report_helpers import send_report

# Initialize clients
client = LangfuseOpenAI()

REPORT_URL = f'{os.getenv("CENTRALA_URL")}/report'
API_KEY = os.getenv('CENTRALA_API_KEY')

# Define available tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "process_image",
            "description": "Process an image with specified operation",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["BRIGHTEN", "DARKEN", "REPAIR"],
                        "description": "Operation to perform on the image"
                    },
                    "image_name": {
                        "type": "string",
                        "description": "Name of the image file to process"
                    }
                },
                "required": ["operation", "image_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_image",
            "description": "Analyze the content of an image and provide description",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Detailed description of what is visible in the image"
                    }
                },
                "required": ["description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_filenames",
            "description": "Extract image filenames from text and add -small suffix",
            "parameters": {
                "type": "object",
                "properties": {
                    "filenames": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of image filenames with -small suffix"
                    }
                },
                "required": ["filenames"]
            }
        }
    }
]

def get_image_as_base64(url: str) -> str:
    """Convert image from URL to base64 string"""
    print(f"\n📥 Downloading image from: {url}")
    response = requests.get(url)
    return base64.b64encode(response.content).decode('utf-8')

def process_image(operation: str, image_name: str):
    """Process image with specified operation and return result"""
    # Ensure we're using -small version
    if not image_name.endswith('-small.PNG'):
        image_name = image_name.replace('.PNG', '-small.PNG')
    
    print(f"\n🔧 Processing image: {image_name} with operation: {operation}")
    response = requests.post(REPORT_URL, json={
        "task": "photos",
        "apikey": API_KEY,
        "answer": f"{operation} {image_name}"
    })
    print(f"📥 Response from processing: {response.json()}")
    return response.json()

def analyze_image(description: str):
    """Store image analysis results"""
    print(f"\n🔍 Storing analysis: {description[:100]}...")
    return {"status": "stored", "description": description}

def extract_filenames(filenames: list):
    """Convert filenames to their -small versions"""
    return {
        "filenames": [
            f"{name.replace('.PNG', '-small.PNG')}" if not name.endswith('-small.PNG') else name
            for name in filenames
        ]
    }

# Start conversation and extract filenames
response = requests.post(REPORT_URL, json={
    "task": "photos",
    "apikey": API_KEY,
    "answer": "START"
})
initial_response = response.json()
print("Initial response:", initial_response)

filename_completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{
        "role": "system",
        "content": "Extract image filenames from the text and convert them to -small versions."
    },
    {
        "role": "user",
        "content": f"Extract image filenames from this response: {initial_response}"
    }],
    tools=tools,
    tool_choice={"type": "function", "function": {"name": "extract_filenames"}}
)

# Get the processed filenames
if filename_completion.choices[0].message.tool_calls:
    images = eval(filename_completion.choices[0].message.tool_calls[0].function.arguments)["filenames"]
else:
    raise Exception("Failed to extract filenames")

print("Processing images:", images)

descriptions = []

print("\n🤖 Starting image analysis process...")
for img in images:
    # Ensure we're using -small version
    img_small = img if img.endswith('-small.PNG') else img.replace('.PNG', '-small.PNG')
    print(f"\n📸 Analyzing image: {img_small}")
    
    # Get base64 of the image
    img_url = f"https://centrala.ag3nts.org/dane/barbara/{img_small}"
    try:
        img_base64 = get_image_as_base64(img_url)
        
        messages = [{
            "role": "system",
            "content": """You are an expert image analyst. Follow these steps strictly:
            1. First suggest an operation (BRIGHTEN/DARKEN/REPAIR) to improve image quality
            2. Always use the process_image function first
            3. Then analyze what you see in the processed image
            Focus ONLY on these key aspects:
            - Hair color and length
            - Eye color and glasses if present
            - Distinctive features (tattoos, scars, etc.)
            - Basic clothing description
            Be concise but precise."""
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Analyze this image: {img_small}. What operation should we try first?"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_base64}"
                    }
                }
            ]
        }]

        print("\n💭 Thinking about initial operation...")
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "process_image"}}
        )

        if completion.choices[0].message.tool_calls:
            tool_call = completion.choices[0].message.tool_calls[0]
            print(f"\n🛠️ Suggested operation: {tool_call.function.arguments}")
            
            args = eval(tool_call.function.arguments)
            # Ensure we're using -small version in the process_image call
            if 'image_name' in args and not args['image_name'].endswith('-small.PNG'):
                args['image_name'] = args['image_name'].replace('.PNG', '-small.PNG')
            
            result = process_image(**args)
            
            # Get base64 of the processed image
            processed_img_url = f"https://centrala.ag3nts.org/dane/barbara/{args['image_name']}"
            processed_img_base64 = get_image_as_base64(processed_img_url)
            
            messages.append({
                "role": "assistant",
                "content": f"Image processed. Result: {result}"
            })
            
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Here's the processed image. Please analyze what you see, focusing on physical characteristics, clothing, and any distinctive features:"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{processed_img_base64}"
                        }
                    }
                ]
            })
            
            print("\n🔍 Analyzing processed image...")
            analysis_completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "analyze_image"}}
            )
            
            if analysis_completion.choices[0].message.tool_calls:
                analysis = eval(analysis_completion.choices[0].message.tool_calls[0].function.arguments)
                descriptions.append(analysis["description"])
                print(f"\n📝 Analysis stored: {analysis['description'][:100]}...")
            else:
                print("❌ No analysis received")
        else:
            print(f"❌ Failed to get operation suggestion for {img_small}")
    except Exception as e:
        print(f"❌ Error processing image {img_small}: {str(e)}")

# Generate final description with more focused prompt
final_prompt = """Based on all the analyzed images, create a concise but detailed description of Barbara in Polish. 
Focus only on the most distinctive and identifying features:
1. Włosy (kolor, długość)
2. Twarz (okulary, makijaż)
3. Charakterystyczne cechy (tatuaże, znamiona)
4. Podstawowy opis sylwetki

Collected descriptions:
{descriptions}

Make the description brief but precise, focusing only on consistent features seen across multiple images."""

print("\n✍️ Generating final description...")
final_completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": final_prompt}]
)

final_description = final_completion.choices[0].message.content
print(f"\n📋 Final description generated: {final_description}")

# Send final report
try:
    print("\n📤 Sending final description to Centrala...")
    response = send_report(final_description, "photos")
    print(f"📨 Report response: {response}")
except Exception as e:
    print(f"❌ Error sending report: {str(e)}")
    raise
