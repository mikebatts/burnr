#openai_api.py

import openai
import os

# Initialize OpenAI API client
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_search_terms(prompt, duration):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": f"Generate search terms and artists for a playlist that matches the following prompt: '{prompt}'"}
            ],
            max_tokens=50
        )
        # Correctly accessing the message content
        search_terms = response['choices'][0]['message']['content'].strip()
        estimated_track_count = duration // 3  # Assuming an average track length of 3 minutes
        return search_terms, estimated_track_count
    except Exception as e:
        print(f"Error generating search terms: {e}")
        return None, 0