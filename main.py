import os
import hmac
import hashlib
import json
from fastapi import FastAPI, Request, HTTPException, Header
from dotenv import load_dotenv
from github import Github, GithubIntegration
import requests

from llm_utils import analyze_code_changes

app = FastAPI()
load_dotenv()

APP_ID = os.environ.get("APP_ID")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")
PRIVATE_KEY_PATH = os.environ.get("PRIVATE_KEY_PATH")

with open(PRIVATE_KEY_PATH) as fin:
    private_key = fin.read()

github_integration = GithubIntegration(APP_ID, private_key)

def generate_hash_signature(secret: bytes, payload: bytes, digest_method=hashlib.sha1):
    return hmac.new(secret, payload, digest_method).hexdigest()

def verify_signature(payload: bytes, x_hub_signature: str):
    secret = WEBHOOK_SECRET.encode("utf-8")
    expected_signature = f"sha1={generate_hash_signature(secret, payload)}"
    if not hmac.compare_digest(expected_signature, x_hub_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

def connect_repo(owner: str, repo_name: str):
    installation_id = github_integration.get_installation(owner, repo_name).id
    access_token = github_integration.get_access_token(installation_id).token
    return Github(login_or_token=access_token).get_repo(f"{owner}/{repo_name}")

@app.post("/webhook")
async def webhook(request: Request, x_hub_signature: str = Header(None)):
    payload = await request.body()
    verify_signature(payload, x_hub_signature)
    payload_dict = json.loads(payload)
    
    if "repository" in payload_dict:
        owner = payload_dict["repository"]["owner"]["login"]
        repo_name = payload_dict["repository"]["name"]
        repo = connect_repo(owner, repo_name)
        
        # Check if it's a pull_request event with action 'opened'
        if payload_dict.get("pull_request") and payload_dict.get("action") == "opened":
            pr_number = payload_dict["pull_request"]["number"]

            #newly added to get pull request diff
            pull_request = repo.get_pull(pr_number)
            diff_url = pull_request.diff_url
            response = requests.get(diff_url)
            #print(response.text)

            print("Before llm call...")

            issue = repo.get_issue(number=pr_number)
            issue.create_comment(
                "Thanks for opening a new PR! Please follow our contributing guidelines to make your PR easier to review."
            )

            # Analyze the code changes
            review_list= analyze_code_changes(response.text)

            # Post each review item as a comment on the PR
            for review in review_list:
                comment_body = (
                    f"**File:** `{review['fileName']}`\n"
                    f"**Code Segment:**\n```\n{review['codeSegmentToFix']}\n```\n"
                    f"**Issue:** {review['comment']}\n"
                    f"**Severity:** {review['severity']}\n"
                    f"**Suggestion:** {review['suggestion']}\n"
                )
                
                # If suggestedCode exists, add it to the comment
                if review.get("suggestedCode"):
                    comment_body += f"```suggestion\n{review['suggestedCode']}\n```"

                issue.create_comment(comment_body)

            # print(review_comments)

            print("After llm call...")

            
    return {}
