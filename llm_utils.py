import os
import openai
from typing import List, Dict
from dotenv import load_dotenv


def analyze_code_changes(diff_content: str) -> List[Dict]:
    """
    Analyze code changes using OpenAI's GPT model
    Returns a list of review comments
    """

    load_dotenv()
    
    openai.api_key = os.environ.get('OPENAI_API_KEY')

    # Prepare the prompt for the LLM
    prompt = f"""
    Analyze the following code changes and provide detailed review comments.
    Focus on:
    - Code quality and best practices
    - Potential security vulnerabilities
    - Performance implications
    - Code style consistency

    Diff content:
    {diff_content}
    """

    # Get analysis from OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an experienced code reviewer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )

    # Parse and format the response
    return (response.choices[0].message.content)