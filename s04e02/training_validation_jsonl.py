import json
import random

def create_training_and_validation_data():
    # Read the files
    with open('correct.txt', 'r') as f:
        correct_numbers = f.read().splitlines()
    
    with open('incorrect.txt', 'r') as f:
        incorrect_numbers = f.read().splitlines()

    # Prepare all data entries
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
    
    # Split into training and validation (80/20 split)
    split_point = int(len(data) * 0.8)
    training_data = data[:split_point]
    validation_data = data[split_point:]
    
    # Write training data
    with open('training_data_80.jsonl', 'w', encoding='utf-8') as f:
        for i, entry in enumerate(training_data):
            json_line = json.dumps(entry, ensure_ascii=False)
            if i < len(training_data) - 1:
                f.write(json_line + '\n')
            else:
                f.write(json_line)
    
    # Write validation data
    with open('validation_data_20.jsonl', 'w', encoding='utf-8') as f:
        for i, entry in enumerate(validation_data):
            json_line = json.dumps(entry, ensure_ascii=False)
            if i < len(validation_data) - 1:
                f.write(json_line + '\n')
            else:
                f.write(json_line)

if __name__ == "__main__":
    create_training_and_validation_data()