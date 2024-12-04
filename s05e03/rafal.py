import asyncio
import aiohttp
import os
import requests
import time
from langfuse.openai import OpenAI

API_URL = "https://rafal.ag3nts.org/b46c3"
API_KEY = os.getenv('CENTRALA_API_KEY')

client = OpenAI()

async def fetch_challenge(session, url):
    start_time = asyncio.get_event_loop().time()
    async with session.get(url) as response:
        result = await response.json()
        end_time = asyncio.get_event_loop().time()
        print(f"📊 Fetch challenge {url}: {end_time - start_time:.2f}s")
        return result

async def process_challenge(session, challenge_url):
    start_time = asyncio.get_event_loop().time()
    
    challenge_text = await fetch_challenge(session, challenge_url)
    task = challenge_text["task"]
    data = challenge_text["data"]
    questions_str = "\n".join(data) if isinstance(data, list) else data

    llm_start_time = asyncio.get_event_loop().time()
    if "pytania" in task:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": """You need to give extremely concise answers to the questions in Polish language.
                Keep each answer as short as possible, ideally 1-3 words.
                Answer each question separately.
                Do not use commas or periods.
                Do not include any explanations.
                For dates, use only numbers.
                For example:
                Q: Jak nazywa się najstarszy hymn Polski?
                A: Bogurodzica
                Q: Kto napisał "Pan Tadeusz"?
                A: Mickiewicz"""
            }, {
                "role": "user",
                "content": questions_str
            }]
        )
        # Split answers into separate items
        result = [ans.strip() for ans in response.choices[0].message.content.split('\n') if ans.strip()]
        
    if "wiedzy" in task:
        file_start = asyncio.get_event_loop().time()
        arxiv_content = await asyncio.to_thread(
            lambda: open('arxiv.md', 'r', encoding='utf-8').read()
        )
        file_end = asyncio.get_event_loop().time()
        print(f"📊 Reading arxiv.md: {file_end - file_start:.2f}s")

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": """You need to answer the questions in Polish language based on the provided arxiv content.
                Keep each answer as short as possible, ideally 1-3 words.
                Answer each question separately.
                Do not use commas or periods.
                Do not include any explanations.
                For example:
                Q: Jaki jest tytuł dokumentu?
                A: Raport 2023"""
            }, {
                "role": "user",
                "content": f"ARXIV CONTENT:\n{arxiv_content}\n\nQUESTIONS:\n{questions_str}"
            }]
        )
        # Split answers into separate items
        result = [ans.strip() for ans in response.choices[0].message.content.split('\n') if ans.strip()]

    llm_end_time = asyncio.get_event_loop().time()
    print(f"📊 LLM processing time: {llm_end_time - llm_start_time:.2f}s")
    
    end_time = asyncio.get_event_loop().time()
    print(f"📊 Total challenge processing time: {end_time - start_time:.2f}s")
    return result

async def main():
    total_start_time = asyncio.get_event_loop().time()
    
    # Initial API calls timing
    auth_start = asyncio.get_event_loop().time()
    password = "NONOMNISMORIAR"
    response = requests.post(API_URL, json={
        "apikey": API_KEY,
        "password": password
    })
    hash = response.json()["message"]

    response = requests.post(API_URL, json={
        "apikey": API_KEY,
        "sign": hash
    })
    signature = response.json()["message"]["signature"]
    timestamp = response.json()["message"]["timestamp"]
    challenges = response.json()["message"]["challenges"]
    auth_end = asyncio.get_event_loop().time()
    print(f"📊 Authentication time: {auth_end - auth_start:.2f}s")

    # Process challenges concurrently
    process_start = asyncio.get_event_loop().time()
    async with aiohttp.ClientSession() as session:
        tasks = [process_challenge(session, challenge) for challenge in challenges]
        all_answers = await asyncio.gather(*tasks)
    process_end = asyncio.get_event_loop().time()
    print(f"📊 Total challenges processing time: {process_end - process_start:.2f}s")

    # Flatten the list of answers if needed
    combined_answers = []
    for answer_set in all_answers:
        if isinstance(answer_set, list):
            combined_answers.extend(answer_set)
        else:
            combined_answers.append(answer_set)

    print("\nCombined answers:", combined_answers)

    # Submit final results
    submit_start = asyncio.get_event_loop().time()
    response = requests.post(API_URL, json={
        "apikey": API_KEY,
        "timestamp": timestamp,
        "signature": signature,
        "answer": combined_answers  # Send as an array
    })
    submit_end = asyncio.get_event_loop().time()
    print(f"📊 Submit results time: {submit_end - submit_start:.2f}s")
    print(response.json())

    total_end_time = asyncio.get_event_loop().time()
    print(f"📊 Total execution time: {total_end_time - total_start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
