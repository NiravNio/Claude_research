#!/usr/bin/env python3
"""
Research top 10 AI updates for today using Claude and commit to GitHub.
This script is run by GitHub Actions daily.
"""

import anthropic
import github
from datetime import datetime
import os

# Get credentials from environment variables (set in GitHub Secrets)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NIRAV_GITHUB_TOKEN = os.getenv("NIRAV_GITHUB_TOKEN")

if not ANTHROPIC_API_KEY or not NIRAV_GITHUB_TOKEN:
    print("❌ Error: ANTHROPIC_API_KEY or NIRAV_GITHUB_TOKEN not set in GitHub Secrets")
    exit(1)

# Initialize clients
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
github_client = github.Github(NIRAV_GITHUB_TOKEN)

# Get repository and today's date
repo = github_client.get_repo()  # Gets the repo where the action is running
today = datetime.now().strftime("%Y-%m-%d")
filename = f"ai-updates/AI-Updates-{today}.md"

print(f"📅 Date: {today}")
print(f"📁 File: {filename}")
print()

# Step 1: Research AI updates with Claude using web search
print("🔍 Researching top 10 AI updates...")
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

# Step 2: Create directory if it doesn't exist (create a placeholder if needed)
# GitHub will create the directory when we create the file in it
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
except anthropic.APIError as e:
    print(f"❌ Claude API error: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    exit(1)

print()
print(f"🎉 Success! AI updates for {today} are now in your repository.")
