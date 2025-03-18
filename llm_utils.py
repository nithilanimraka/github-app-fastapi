import os
from openai import OpenAI
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


api_key = os.environ.get('OPENAI_API_KEY')

client = OpenAI(api_key=api_key)

class ReviewModel(BaseModel):
    class Step(BaseModel):
        fileName: str = Field(description="The name of the file that has an issue")
        start_line_with_prefix: str = Field(description="The starting line number in the file (REQUIRED). \
                                            If the start_line is from the new file, indicate it with a '+' prefix, or if it is from the old file, indicate it with a '-' prefix")
        end_line_with_prefix: str = Field(description="The ending line number in the file (REQUIRED). \
                                          If the end_line is from the new file, indicate it with a '+' prefix, or if it is from the old file, indicate it with a '-' prefix")
        language: str = Field(description="The language of the code segment")
        codeSegmentToFix: str = Field(description="The code segment that needs to be fixed from code diff in diff style('+' for added, '-' for removed, or nothing for normal code)")
        comment: str = Field(description="The comment on the code segment")
        suggestion: str = Field(description="The suggestion to fix the code segment")
        suggestedCode: Optional[str] = Field(None, description="The updated code segment for the fix")
        severity: str = Field(description="The severity of the issue. Can be 'error', 'warning', or 'info'")

    steps: list[Step]

def analyze_code_changes(structured_diff_text: str) -> List[Dict]:
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
    - Always output the codeSegmentToFix in the diff format (e.g., '+ added code', '- removed code', 'or nothing for normal code').
    - If there is a new line in the codeSegmentToFix (when there are multiple lines), you MUST indicate it with the new line symbol.
    - Ensure that you provide all the necessary code lines in the codeSegmentToFix field.
    - If there are multiple comments for the same code segment, provide the comments separated by commas.

    CRITICAL REQUIREMENTS:
    - Precisely mention the position where the comment should be placed.
    - The codeSegmentToFix should exactly start from the start_line_with_prefix and end at the end_line_with_prefix.
    - Use the file-based line numbers provided in the structured diff below.
    - You MUST provide exact start_line_with_prefix and end_line_with_prefix numbers for each comment.
    - Never omit line numbers or the system will fail.

    Examples for start_line_with_prefix when the start_line is from new file: "+5, +2, +51, +61" 
    Examples for start_line_with_prefix when the start_line is from old file: "-8, -1, -56, -20" 

    Examples for end_line_with_prefix when the start_line is from new file: "+10, +2, +77, +65" 
    Examples for end_line_with_prefix when the start_line is from old file: "-1, -5, -22, -44" 

    Diff content:
    {structured_diff_text}
    """

    print("Before API CALL...")

    # Get analysis from OpenAI
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are an experienced code reviewer."},
            {"role": "user", "content": prompt}
        ],
        response_format=ReviewModel,
    )

    print("After API CALL...")

    # Parse and format the response
    response_pydantic= completion.choices[0].message.parsed

    review_steps = []
    
    for step in response_pydantic.steps:

        value1 = step.start_line_with_prefix
        start_line = int(value1.replace("+", "").strip())  # Remove '+' and strip spaces

        value2 = step.end_line_with_prefix
        end_line = int(value2.replace("+", "").strip()) 

        step_dict = {
            "fileName": step.fileName,
            "start_line": start_line, 
            "start_line_with_prefix": step.start_line_with_prefix, 
            "end_line": end_line,      
            "end_line_with_prefix": step.end_line_with_prefix, 
            "language": step.language,
            "codeSegmentToFix": step.codeSegmentToFix,
            "comment": step.comment,
            "suggestion": step.suggestion,
            "suggestedCode": step.suggestedCode,
            "severity": step.severity
        }
        review_steps.append(step_dict)

    return review_steps 
