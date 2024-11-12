from langfuse.openai import OpenAI
from pathlib import Path

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
