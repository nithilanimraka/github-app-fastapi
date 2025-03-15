import os
from openai import OpenAI
from typing import List, Dict
from dotenv import load_dotenv

client = OpenAI()


def analyze_code_changes(diff_content: str) -> List[Dict]:
    """
    Analyze code changes using OpenAI's GPT model
    Returns a list of review comments
    """

    load_dotenv()
    
    # openai.api_key = os.environ.get('OPENAI_API_KEY')

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
    response = client.responses.create(
        model="gpt-4o",
        input=[
            {"role": "system", "content": "You are an experienced code reviewer."},
            {"role": "user", "content": prompt}
        ]
    )

    # Parse and format the response
    return (response.choices[0].message.content)