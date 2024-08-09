from openai import OpenAI
import os

# Instantiate the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_prompt_response(prompt):
    try:
        # Using the new API for completion
        response = client.completions.create(
            model="gpt-4o",  # or whichever model you prefer
            prompt=prompt,
            max_tokens=50
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error generating prompt response: {e}")
        return None