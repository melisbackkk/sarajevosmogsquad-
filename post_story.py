#!/usr/bin/env python3
import os
import sys
import time
import requests
from pathlib import Path


def get_credentials():
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    user_id = os.getenv("INSTAGRAM_USER_ID")
    
    if not access_token:
        raise ValueError("INSTAGRAM_ACCESS_TOKEN environment variable not set")
    if not user_id:
        raise ValueError("INSTAGRAM_USER_ID environment variable not set")
    
    return access_token.strip(), user_id.strip()


def validate_story_file(filename: str) -> Path:
    file_path = Path("stories") / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"Not a file: {file_path}")
    
    return file_path


def get_github_image_url(filename: str) -> str:
    # Get repository info from environment (set by GitHub Actions)
    repo = os.getenv("GITHUB_REPOSITORY", "melisbackkk/sarajevosmogsquad-")  # format: owner/repo
    branch = os.getenv("GITHUB_REF_NAME", "main")  # default to main
    
    if not repo:
        raise ValueError("GITHUB_REPOSITORY environment variable not set")
    
    # Construct GitHub raw content URL
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/stories/{filename}"
    return url


def sanitize_error_message(message: str, access_token: str) -> str:
    return message.replace(access_token, "***REDACTED***")


def post_story_to_instagram(image_url: str, access_token: str, user_id: str) -> str:
    # Create story container
    container_url = f"https://graph.facebook.com/v21.0/{user_id}/media"
    container_payload = {
        "image_url": image_url,
        "media_type": "STORIES",
        "access_token": access_token,
    }
    
    print("Creating story container...")
    response = requests.post(container_url, data=container_payload)
    
    if response.status_code != 200:
        safe_message = sanitize_error_message(response.text, access_token)
        print(f"Error: {response.status_code} - {safe_message}")
        response.raise_for_status()
    
    container_id = response.json().get("id")
    print(f"Container created: {container_id}")
    
    # Wait for Instagram to process
    print("Waiting for Instagram to process...")
    time.sleep(3)
    
    # Publish story
    publish_url = f"https://graph.facebook.com/v21.0/{user_id}/media_publish"
    publish_payload = {
        "creation_id": container_id,
        "access_token": access_token,
    }
    
    print("Publishing story...")
    response = requests.post(publish_url, data=publish_payload)
    
    if response.status_code != 200:
        safe_message = sanitize_error_message(response.text, access_token)
        print(f"Error: {response.status_code} - {safe_message}")
        response.raise_for_status()
    
    media_id = response.json().get("id")
    print(f"Story published: {media_id}")
    
    return media_id


def main():
    if len(sys.argv) != 2:
        print("Usage: python post_story.py <filename>")
        print("Example: python post_story.py 2025-12-19_14.jpg")
        print("\nNote: File must exist in stories/ directory")
        print("      Image will be posted from GitHub repository")
        return 1
    
    filename = sys.argv[1]
    
    try:
        print(f"Validating file: {filename}")
        file_path = validate_story_file(filename)
        print(f"File found: {file_path}")
        
        print("\nConstructing GitHub URL...")
        image_url = get_github_image_url(filename)
        print(f"Image URL: {image_url}")
        
        print("\nGetting credentials...")
        access_token, user_id = get_credentials()
        
        print("\nPosting to Instagram...")
        media_id = post_story_to_instagram(image_url, access_token, user_id)
        
        print(f"\nSuccess! Story posted with media ID: {media_id}")
        
    except Exception as e:
        # Sanitize error message to prevent token leakage in CI logs
        error_msg = str(e)
        try:
            # Only sanitize if we have a token
            if 'access_token' in locals():
                error_msg = sanitize_error_message(error_msg, access_token)
        except:
            pass  # If sanitization fails, use original message
        print(f"Error: {error_msg}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
