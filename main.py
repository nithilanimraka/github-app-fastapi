import os
import time
import jwt
import httpx
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configuration
APP_ID = os.getenv("APP_ID")
# WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
PRIVATE_KEY_PATH = "app.pem"

# Load private key
with open(PRIVATE_KEY_PATH, "r") as f:
    PRIVATE_KEY = f.read()

async def create_github_jwt():
    now = int(time.time())
    payload = {
        "iat": now,
        "exp": now + (10 * 60),  # 10 minutes
        "iss": APP_ID
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")

async def get_installation_token(installation_id: int):
    jwt_token = await create_github_jwt()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        response.raise_for_status()
        return response.json()["token"]

@app.post("/webhook")
async def handle_webhook(request: Request):
    # Verify signature
    body = await request.body()
    signature = request.headers.get("x-hub-signature-256", "").split("sha256=")[-1]
    expected_signature = jwt.encode({"data": body}, algorithm="HS256")
    
    if not jwt.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process event
    event = request.headers.get("x-github-event")
    payload = await request.json()

    if event == "pull_request" and payload["action"] == "opened":
        installation_id = payload["installation"]["id"]
        repo = payload["repository"]
        pr_number = payload["pull_request"]["number"]
        
        # Get access token
        access_token = await get_installation_token(installation_id)
        
        # Post comment
        comment_url = f"https://api.github.com/repos/{repo['owner']['login']}/{repo['name']}/issues/{pr_number}/comments"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                comment_url,
                json={"body": "Hello World!"},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            response.raise_for_status()
    
    return {"status": "processed"}