from langfuse.openai import OpenAI

def get_openai_answer(question):
    try:
        client = OpenAI()

        print(f"Debug: Generating answer for question: '{question}'")
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Specify the model you want to use
            messages=[
                {"role": "system", "content": "Please provide a single-word answer."},  # System message
                {"role": "user", "content": question}
            ]
        )
        
        # Extract the answer from the response
        answer = response.choices[0].message.content.strip()
        print(f"Debug: OpenAI response: '{answer}'")
        return answer
    except Exception as e:
        print(f"Error getting answer from OpenAI for question '{question}': {e}")
        raise 
