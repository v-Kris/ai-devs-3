from langfuse.openai import OpenAI
from pathlib import Path
import base64
import os
import requests


def get_openai_answer(question):
    try:
        client = OpenAI()

        print(f"Debug: Generating answer for question: '{question}'")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Please provide a single-word answer."},
                {"role": "user", "content": question}
            ]
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"Debug: OpenAI response: '{answer}'")
        return answer
    except Exception as e:
        print(f"Error getting answer from OpenAI for question '{question}': {e}")
        raise

def transcribe_audio(audio_file):
    """Transcribe audio file using OpenAI Whisper"""
    try:
        client = OpenAI()
        
        print(f"Debug: Transcribing audio file: {audio_file}")
        with open(audio_file, "rb") as file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=file,
                language="pl"  # Polish language
            )
        
        transcript = response.text
        print(f"Debug: Transcription complete. Length: {len(transcript)} characters")
        return transcript
    except Exception as e:
        print(f"Error transcribing audio file '{audio_file}': {e}")
        raise

def chat_with_gpt(system_message, user_message):
    """Chat with GPT using specified system and user messages"""
    try:
        client = OpenAI()
        
        print(f"Debug: Sending chat message to GPT")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"Debug: GPT response received. Length: {len(answer)} characters")
        return answer
    except Exception as e:
        print(f"Error in chat_with_gpt: {e}")
        raise

class VisionAI:
    def __init__(self):
        self.client = OpenAI()

    def encode_image_to_base64(self, image_path):
        """Convert image to base64 string"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_image(self, image_path, prompt):
        """
        Analyze an image using GPT-4o-mini
        Args:
            image_path: Path to the image file
            prompt: Prompt for the vision model
        Returns:
            str: Analysis response from the model
        """
        base64_image = self.encode_image_to_base64(image_path)

        print(f"Debug: Analyzing image: {image_path}")
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )

        analysis = response.choices[0].message.content.strip()
        print(f"Debug: Image analysis complete. Length: {len(analysis)} characters")
        return analysis

def create_jina_embedding(text):
    try:
        response = requests.post(
            'https://api.jina.ai/v1/embeddings',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {os.getenv("JINA_API_KEY")}'
            },
            json={
                'model': 'jina-embeddings-v3',
                'task': 'text-matching',
                'dimensions': 1024,
                'late_chunking': False,
                'embedding_type': 'float',
                'input': [text]
            }
        )

        response.raise_for_status()  # Raise an error for bad responses

        data = response.json()
        return data['data'][0]['embedding']
    except requests.exceptions.RequestException as error:
        print("Error creating Jina embedding:", error)
        raise 
