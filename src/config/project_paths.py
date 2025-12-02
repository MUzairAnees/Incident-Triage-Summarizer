# We made this file so that we can import the .env path always into other code files
# This file lives in project_root/src/config/project_paths.py
# so parents[2] gives us the project_root path (starting from index 0)
# parents[0]: config/
# parents[1]: src/
# parents[2]: project_root/

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"