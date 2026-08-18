import json
import os
import subprocess
from collections import defaultdict

OWNER = os.environ["GITHUB_REPOSITORY_OWNER"]
README = "README.md"

BAR_LENGTH = 20
TOP_LANGUAGES = 6

def gh_api(endpoint):
    result = subprocess.run(
        ["gh", "api", endpoint],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def get_repositories():
    repos = []
    page = 1

    while True:
        data = gh_api(
            f"users/{OWNER}/repos?per_page=100&page={page}&type=owner"
        )

        if not data:
            break

        repos.extend(
            repo["name"]
            for repo in data
            if not repo["fork"]
        )

        page += 1

    return repos


def get_language_stats(repos):
    languages = defaultdict(int)

    for repo in repos:
        print(f"Reading {repo}...")

        data = gh_api(f"repos/{OWNER}/{repo}/languages")

        for language, bytes_count in data.items():
            languages[language] += bytes_count

    return languages


def make_bar(percentage):
    filled = round((percentage / 100) * BAR_LENGTH)
    filled = max(0, min(BAR_LENGTH, filled))

    return "█" * filled + "░" * (BAR_LENGTH - filled)


def generate_block(languages):
    total = sum(languages.values())

    if total == 0:
        return "languages\n\nNo language data available."

    top = sorted(
        languages.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:TOP_LANGUAGES]

    lines = ["languages", ""]

    for language, byte_count in top:
        percentage = (byte_count / total) * 100
        bar = make_bar(percentage)

        lines.append(
            f"{language:<13} {bar}  {percentage:5.1f}%"
        )

    return "\n".join(lines)


def update_readme(block):
    with open(README, "r", encoding="utf-8") as file:
        content = file.read()

    start_marker = "<!-- LANGUAGES:START -->"
    end_marker = "<!-- LANGUAGES:END -->"

    start = content.find(start_marker)
    end = content.find(end_marker)

    if start == -1 or end == -1:
        raise RuntimeError(
            "Could not find LANGUAGES markers in README.md"
        )

    start_content = start + len(start_marker)

    new_content = (
        content[:start_content]
        + "\n\n```text\n"
        + block
        + "\n```\n"
        + content[end:]
    )

    with open(README, "w", encoding="utf-8") as file:
        file.write(new_content)


repos = get_repositories()

print(f"Found {len(repos)} repositories.")

languages = get_language_stats(repos)

block = generate_block(languages)

print("\nGenerated:\n")
print(block)

update_readme(block)

print("\nREADME updated.")