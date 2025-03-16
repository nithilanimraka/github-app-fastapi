import os
from openai import OpenAI
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


api_key = os.environ.get('OPENAI_API_KEY')

client = OpenAI(api_key=api_key)

class ReviewModel(BaseModel):
    class Step(BaseModel):
        fileName: str = Field(description="The name of the file that has an issue")
        language: str = Field(description="The language of the code segment")
        codeSegmentToFix: str = Field(description="The code segment that needs to be fixed from code diff in diff style('+' for added, '-' for removed, or nothing for normal code)")
        comment: str = Field(description="The comment on the code segment")
        suggestion: str = Field(description="The suggestion to fix the code segment")
        suggestedCode: Optional[str] = Field(None, description="The updated code segment for the fix")
        severity: str = Field(description="The severity of the issue. Can be 'error', 'warning', or 'info'")

    steps: list[Step]

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

    Important:
    - Provide insights in the comment section for each code segment. Provide improvements in suggestions when necessary.
    - Always output the code segment to fix in the diff format (e.g., '+ added code', '- removed code', 'or nothing for normal code').
    - Ensure that you provide all the necessary code lines in the codeSegmentToFix field.
    - If there are multiple comments for the same code segment, provide the comments separated by commas.

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
    response_pydantic= completion.choices[0].message.parsed

    review_steps = []
    
    for step in response_pydantic.steps:
        step_dict = {
            "fileName": step.fileName,
            "language": step.language,
            "codeSegmentToFix": step.codeSegmentToFix,
            "comment": step.comment,
            "suggestion": step.suggestion,
            "suggestedCode": step.suggestedCode,
            "severity": step.severity
        }
        review_steps.append(step_dict)

    for review in review_steps:
        print(review)
        print("\n\n")

    return review_steps 
