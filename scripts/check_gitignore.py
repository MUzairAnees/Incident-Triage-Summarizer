# Check which files will be ignored by Git and which won't
# Run after creating your .gitignore file in the project root

import subprocess
import os
from pathlib import Path

def check_git_status():
    # Checking which files Git will track
    print("Files that WILL be committed to GitHub:")
    print("="*50)

    # get the list of tracked files:
    result = subprocess.run(["git", "ls-files"], capture_output=True, text=True)

    if result.returncode == 0:
        tracked_files = result.stdout.strip().split("\n")
        for file in tracked_files:
            if file:
                print(file)

    print("\nFiles that will be IGNORED (not committed):")
    print("="*50)

    # checking specific important files
    files_to_check = [
        ".env",
        "venv/",
        "__pycache__/",
        "*.db",
        ".idea/"
    ]

    for pattern in files_to_check:
        if pattern.endswith("/"):
            exists = Path(pattern.rstrip("/")).is_file()
        elif '*' in pattern:
            exists = len(list(Path().glob(pattern))) > 0
        else:
            exists = Path(pattern).exists()

        if exists:
            print(f"{pattern}: (exists and will be ignored)")
        else:
            print(f"{pattern}: NOT FOUND")

    # check if .env is accidentally staged to be committed
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)

    if ".env" in result.stdout:
        print("\nWarning: .env file might be staged to be committed to GitHub.")
        print("Run: git rm --cached .env")

if __name__ == "__main__":
    if not Path(".git").exists():
        print("Not in a git repository yet!")
        print("Please run: git init")
    else:
        check_git_status()