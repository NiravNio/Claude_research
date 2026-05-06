#!/usr/bin/env python3
"""
Research top 10 AI updates for today using Claude and commit to GitHub.
This script is run by GitHub Actions daily.
Includes automatic retry logic for API rate limits and temporary failures.
"""

import anthropic
import github
from datetime import datetime
import os
import time

# Get credentials from environment variables (set in GitHub Secrets)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")  # Automatically set by GitHub Actions

if not ANTHROPIC_API_KEY or not GITHUB_TOKEN or not REPO_NAME:
    print("❌ Error: Missing required environment variables")
    print(f"  ANTHROPIC_API_KEY: {bool(ANTHROPIC_API_KEY)}")
    print(f"  GITHUB_TOKEN: {bool(GITHUB_TOKEN)}")
    print(f"  GITHUB_REPOSITORY: {bool(REPO_NAME)}")
    exit(1)

# Initialize clients with modern PyGithub syntax
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
github_client = github.Github(auth=github.Auth.Token(GITHUB_TOKEN))

# Get repository and today's date
repo = github_client.get_repo(REPO_NAME)  # Use the repository name from GitHub Actions
today = datetime.now().strftime("%Y-%m-%d")
filename = f"ai-updates/AI-Updates-{today}.md"

print(f"📅 Date: {today}")
print(f"📁 File: {filename}")
print(f"📦 Repository: {REPO_NAME}")
print()

# Step 1: Research AI updates with Claude using web search (with retry logic)
print("🔍 Researching top 10 AI updates...")

max_retries = 3
retry_count = 0
content = None

while retry_count < max_retries and content is None:
    try:
        message = anthropic_client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": f"""Research the top 10 AI updates and announcements from today ({today}).

Please format your response as markdown with:
1. A title with today's date
2. A numbered list of the 10 most important AI updates
3. For each update include:
   - Title (bold)
   - Brief description (2-3 sentences)
   - Source/where you found it

Focus on significant announcements, product launches, research breakthroughs, and industry news.
Make it professional and well-organized."""
                }
            ]
        )
        content = message.content[0].text
        print("✅ Research complete")
        print()
        
    except anthropic.RateLimitError as e:
        retry_count += 1
        if retry_count < max_retries:
            wait_time = 2 ** retry_count  # Exponential backoff: 2, 4, 8 seconds
            print(f"⏳ Rate limit hit. Retrying in {wait_time} seconds... (Attempt {retry_count}/{max_retries})")
            time.sleep(wait_time)
        else:
            print(f"❌ Rate limit error after {max_retries} retries: {e}")
            exit(1)
            
    except anthropic.APIStatusError as e:
        if e.status_code == 529:  # Overloaded error
            retry_count += 1
            if retry_count < max_retries:
                wait_time = 5 * retry_count  # Longer wait for overload: 5, 10, 15 seconds
                print(f"⏳ API overloaded. Retrying in {wait_time} seconds... (Attempt {retry_count}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"❌ API overloaded after {max_retries} retries. Please try again later.")
                exit(1)
        else:
            print(f"❌ API error: {e}")
            exit(1)
            
    except anthropic.APIError as e:
        print(f"❌ Claude API error: {e}")
        exit(1)

if content is None:
    print("❌ Failed to get content after retries")
    exit(1)

# Step 2: Create or update the file
print("📤 Pushing to GitHub...")

try:
    # Try to get the file if it already exists
    try:
        file = repo.get_contents(filename)
        # File exists, update it
        repo.update_file(
            path=filename,
            message=f"Update AI updates for {today}",
            content=content,
            sha=file.sha
        )
        print(f"✅ Updated: {filename}")
    except github.GithubException as e:
        if e.status == 404:
            # File doesn't exist, create it
            repo.create_file(
                path=filename,
                message=f"Add AI updates for {today}",
                content=content
            )
            print(f"✅ Created: {filename}")
        else:
            raise

except github.GithubException as e:
    print(f"❌ GitHub error: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    exit(1)

print()
print(f"🎉 Success! AI updates for {today} are now in your repository.")
