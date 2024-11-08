import requests

def get_ollama_answer(prompt):
    """Local LLM using Ollama"""
    try:
        print(f"Debug: Sending prompt to Ollama: {prompt}")
        
        response = requests.post('http://localhost:11434/api/generate',
                               json={
                                   "model": "gemma2:2b",
                                   "prompt": prompt,
                                   "stream": False
                               })
        response.raise_for_status()
        answer = response.json()['response'].strip()
        
        print(f"Debug: Ollama response: {answer}")
        return answer
    except Exception as e:
        print(f"Error getting answer from Ollama: {e}")
        raise 
