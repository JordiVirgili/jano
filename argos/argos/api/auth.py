import os
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
import secrets
from dotenv import load_dotenv

# Get credentials from environment variables
load_dotenv()
API_USERNAME = os.getenv("JANO_API_USERNAME")
API_PASSWORD = os.getenv("JANO_API_PASSWORD")

security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    Verify the HTTP Basic Auth credentials.
    Returns the username if valid, raises HTTPException otherwise.
    """
    is_username_correct = secrets.compare_digest(credentials.username, API_USERNAME)
    is_password_correct = secrets.compare_digest(credentials.password, API_PASSWORD)

    if not (is_username_correct and is_password_correct):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"}, )

    return credentials.username