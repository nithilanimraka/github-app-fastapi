import os
from openai import OpenAI
from typing import List, Dict
from pydantic import BaseModel


api_key = os.environ.get('OPENAI_API_KEY')

client = OpenAI(api_key=api_key)

class ReviewModel(BaseModel):
    fileName: list[str]
    codeSegmentToFix: list[str]
    comment: list[str]
    suggestion: list[str]


def analyze_code_changes(diff_content: str) -> List[Dict]:
    """
    Analyze code changes using OpenAI's GPT model
    Returns a list of review comments
    """

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
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are an experienced code reviewer."},
            {"role": "user", "content": prompt}
        ],
        response_format=ReviewModel,
    )

    # Parse and format the response
    return (completion.choices[0].message.parsed)