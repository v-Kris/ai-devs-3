import json
import random

def create_training_jsonl():
    # Read the files
    with open('correct.txt', 'r') as f:
        correct_numbers = f.read().splitlines()
    
    with open('incorrect.txt', 'r') as f:
        incorrect_numbers = f.read().splitlines()

    # Prepare data entries
    data = []
    
    # Add correct numbers (label "1")
    for number in correct_numbers:
        entry = {
            "messages": [
                {"role": "system", "content": "Validate numbers"},
                {"role": "user", "content": number},
                {"role": "assistant", "content": "1"}
            ]
        }
        data.append(entry)
    
    # Add incorrect numbers (label "0")
    for number in incorrect_numbers:
        entry = {
            "messages": [
                {"role": "system", "content": "Validate numbers"},
                {"role": "user", "content": number},
                {"role": "assistant", "content": "0"}
            ]
        }
        data.append(entry)
    
    # Shuffle the data
    random.shuffle(data)
    
    # Write to JSONL file
    with open('training_data.jsonl', 'w', encoding='utf-8') as f:
        for i, entry in enumerate(data):
            json_line = json.dumps(entry, ensure_ascii=False)
            # Add newline only if it's not the last entry
            if i < len(data) - 1:
                f.write(json_line + '\n')
            else:
                f.write(json_line)

if __name__ == "__main__":
    create_training_jsonl()
