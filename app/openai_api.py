import openai
import os

# Initialize OpenAI API key (ensure your API key is set in the environment variables)
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_prompt_response(prompt):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=50
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error generating prompt response: {e}")
        return None