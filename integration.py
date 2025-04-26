#!/usr/bin/env python3
"""
Jano Integration - Connects Argos (defender) and Eris (attacker)

This script demonstrates how Argos and Eris can work together to:
1. Identify services running on a system
2. Analyze their configurations
3. Test them for vulnerabilities
4. Generate comprehensive security reports
"""

import argparse
import requests
import json
import sys
import time
from typing import Dict, Any, List, Optional
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
ARGOS_API_URL = os.getenv("ARGOS_API_URL", "http://localhost:8005/api/v1")
ERIS_API_URL = os.getenv("ERIS_API_URL", "http://localhost:8006/api/v1")
API_USERNAME = os.getenv("JANO_API_USERNAME", "admin")
API_PASSWORD = os.getenv("JANO_API_PASSWORD", "secure_password_here")


def get_auth_header():
    """Generate the HTTP basic auth header."""
    credentials = f"{API_USERNAME}:{API_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded_credentials}"}


def api_request(method: str, url: str, data: Optional[Dict[str, Any]] = None):
    """Make an API request to either Argos or Eris."""
    headers = {**get_auth_header(), "Content-Type": "application/json"}

    try:
        if method.lower() == "get":
            response = requests.get(url, headers=headers)
        elif method.lower() == "post":
            response = requests.post(url, headers=headers, json=data)
        else:
            print(f"Unsupported method: {method}")
            return None

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request error: {str(e)}")
        return None


def create_chat_session():
    """Create a new chat session in Argos."""
    result = api_request("post", f"{ARGOS_API_URL}/chat/new")
    if result and "session_id" in result:
        return result["session_id"]
    return None


def send_chat_message(session_id: str, message: str, advanced: bool = False):
    """Send a message to the Argos chat API."""
    data = {"message": message, "session_id": session_id, "force_advanced": advanced}
    return api_request("post", f"{ARGOS_API_URL}/chat/query", data)


def run_security_assessment(target: str, service: str):
    """
    Run a complete security assessment using both Argos and Eris.

    Args:
        target: Hostname or IP address to assess
        service: Service type to test (e.g., "ssh", "http")
    """
    print(f"\n{'=' * 80}\nJANO SECURITY ASSESSMENT\n{'=' * 80}")
    print(f"Target: {target}")
    print(f"Service: {service}")
    print(f"{'=' * 80}\n")

    # Step 1: Start a conversation with Argos
    print("Creating chat session with Argos...")
    session_id = create_chat_session()
    if not session_id:
        print("Failed to create chat session")
        return

    print(f"Session created: {session_id}")

    # Step 2: Ask Argos for configuration best practices
    print("\n[STEP 1] Consulting Argos for secure configuration best practices...")
    query = f"What are the security best practices for configuring {service}? Focus on the most critical security settings."

    response = send_chat_message(session_id, query, True)
    if response and "message" in response:
        print("\nArgos recommends:")
        print(f"{'-' * 80}\n{response['message']}\n{'-' * 80}")
    else:
        print("Failed to get recommendations from Argos")

    # Step 3: Run an attack simulation with Eris
    print("\n[STEP 2] Running attack simulation with Eris...")
    plugin_name = f"weak{service}plugin"  # Assuming naming convention

    attack_result = api_request("post", f"{ERIS_API_URL}/eris/attack/{plugin_name}?target={target}", {})

    if attack_result and "result" in attack_result:
        result = attack_result["result"]

        print("\nEris attack simulation results:")
        print(f"{'-' * 80}")
        print(f"Success: {result.get('success', False)}")
        print(f"Severity: {result.get('severity', 'unknown')}")
        print(f"\nDetails: {result.get('details', 'No details available')}")

        if "recommendations" in result:
            print("\nRecommendations:")
            for i, rec in enumerate(result["recommendations"], 1):
                print(f"  {i}. {rec}")
        print(f"{'-' * 80}")
    else:
        print("Failed to run attack simulation or no results returned")

    # Step 4: Send attack results to Argos for analysis
    if attack_result and "result" in attack_result:
        print("\n[STEP 3] Sending attack results to Argos for analysis...")

        result_json = json.dumps(attack_result["result"], indent=2)
        query = f"I ran a security test against my {service} service on {target}. Here are the results:\n\n```json\n{result_json}\n```\n\nCan you explain these findings and provide detailed steps to fix these issues?"

        response = send_chat_message(session_id, query, True)
        if response and "message" in response:
            print("\nArgos analysis of attack results:")
            print(f"{'-' * 80}\n{response['message']}\n{'-' * 80}")
        else:
            print("Failed to get analysis from Argos")

    print(f"\n{'=' * 80}\nAssessment Complete\n{'=' * 80}")
    print(f"Chat session ID: {session_id} (you can continue this conversation in the Argos chat interface)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jano Security Assessment Integration Tool")
    parser.add_argument("target", help="Target hostname or IP address")
    parser.add_argument("service", help="Service to assess (e.g., ssh, http)")

    args = parser.parse_args()

    try:
        run_security_assessment(args.target, args.service)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)