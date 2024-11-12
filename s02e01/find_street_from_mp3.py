import os
from pathlib import Path
from common.ai_helpers import transcribe_audio, chat_with_gpt
from common.report_helpers import send_report

def transcribe_audio_files(directory):
    """Transcribe all audio files in the given directory using OpenAI Whisper"""
    transcriptions = []
    
    for file in Path(directory).glob("*"):
        if file.suffix.lower() in ['.mp3', '.wav', '.m4a']:
            print(f"Transcribing {file.name}...")
            transcript = transcribe_audio(file)
            transcriptions.append(transcript)
    
    return transcriptions

def analyze_location(transcriptions):
    """Analyze transcriptions to find Andrzej Maj's workplace location"""
    combined_context = "\n\n".join(transcriptions)
    
    analysis_prompt = f"""Based on the following witness statements, I need to determine where Professor Andrzej Maj teaches.
    
Context from transcriptions:
{combined_context}

Please think through this step by step:
1. What information do we have about Andrzej Maj and his workplace?
2. Is there any mention of the university's history or royal connections?
3. What specific institutes or departments are mentioned in the context?
4. Based on the historical context and institute mentions, which university building/institute does he most likely work at?
5. What is the specific street address of this institute?

Provide a detailed analysis of your findings, paying special attention to any historical references or specific institute names mentioned.
"""

    detailed_analysis = chat_with_gpt(
        system_message="You are a helpful detective analyzing witness statements. Focus on historical context and specific institute locations within older, established universities. Pay special attention to royal or historical connections.",
        user_message=analysis_prompt
    )
    
    print("\nDetailed Analysis:")
    print(detailed_analysis)
    
    street_prompt = f"""Based on your previous analysis:

{detailed_analysis}

Podaj nam proszę TYLKO nazwę ulicy (bez numeru), na której znajduje się instytut. 
Odpowiedź ma zawierać wyłącznie nazwę ulicy, bez żadnych dodatkowych słów czy wyjaśnień."""

    street_name = chat_with_gpt(
        system_message="You are a precise assistant. Provide ONLY the street name, nothing else.",
        user_message=street_prompt
    )
    
    return street_name.strip()

def main():
    # Directory containing the audio files
    audio_dir = "przesluchania"
    transcriptions_file = "transcriptions.txt"
    
    # Check if transcriptions file already exists
    if os.path.exists(transcriptions_file):
        print("Found existing transcriptions file, loading it...")
        with open(transcriptions_file, "r", encoding="utf-8") as f:
            content = f.read()
            transcriptions = [
                trans.strip() 
                for trans in content.split("Transcription")[1:]
                if trans.strip()
            ]
            transcriptions = [
                trans.split(":", 1)[1].strip() 
                for trans in transcriptions
            ]
    else:
        print("No existing transcriptions found, transcribing audio files...")
        transcriptions = transcribe_audio_files(audio_dir)
        
        with open(transcriptions_file, "w", encoding="utf-8") as f:
            for i, trans in enumerate(transcriptions, 1):
                f.write(f"Transcription {i}:\n{trans}\n\n")
    
    # Analyze the location
    result = analyze_location(transcriptions)
    print("\nAnalysis Result:")
    print(result)
    
    # Send the report
    response = send_report(result, "mp3")
    print(f"Debug: API Response: {response}")

if __name__ == "__main__":
    main() 
