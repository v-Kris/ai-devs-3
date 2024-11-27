import os
from langfuse.openai import OpenAI
from common.report_helpers import send_report

# Initialize Langfuse OpenAI client
client = OpenAI()

# Get fine-tuned model name from env
FT_MODEL = os.getenv('FT_MODEL')

def validate_numbers():
    # Read verify.txt
    with open('verify.txt', 'r') as f:
        lines = f.read().splitlines()
    
    correct_indexes = []
    
    # Process each line
    for line in lines:
        # Split line by '=' to get index and numbers
        index, numbers = line.split('=')
        
        # Validate the entire numbers string
        completion = client.chat.completions.create(
            model=FT_MODEL,
            messages=[
                {"role": "system", "content": "Validate numbers"},
                {"role": "user", "content": numbers.strip()}
            ]
        )
        
        # Get validation result (0 or 1)
        result = completion.choices[0].message.content
        if result == "1":
            correct_indexes.append(index)
    
    # Send the list of indexes directly
    answer = correct_indexes
    print(f"Correct indexes: {answer}")
    
    try:
        print("\n📤 Sending validation results to Centrala...")
        response = send_report(answer, "research")
        print(f"📨 Report response: {response}")
    except Exception as e:
        print(f"❌ Error sending report: {str(e)}")
        raise

if __name__ == "__main__":
    validate_numbers()
