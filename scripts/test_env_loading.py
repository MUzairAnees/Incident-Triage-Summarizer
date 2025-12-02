# This is a python file to check our .env file
# It serves us as an educational script-- Not actually a real test that would go in the tests folder
# That is for pytest only

import os
import sys
from pathlib import Path
from dotenv import load_dotenv      # <-- loading of your .env file happens here!

def test_env_loading():
    # Tell python where to find the file next
    # this goes up 2 levels: this file -> /scripts directory -> project directory (aka project_root)
    project_root = Path(__file__).parent.parent

    # sys.path is a list item, so what were saying here is that please insert this path item at index 0 of the sys.path list
    # and then sys.path also searches through the list (there's other items in there, read docs for more info) and adds imports
    # to the python path so that they work
    sys.path.insert(0, str(project_root))

    # load the .env file from the project root
    env_file = project_root / '.env'

    # check if it exists. if not then show details of current directory and project root directory
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loading environment from {env_file}")
    else:
        print(f"X Environment not found at: {env_file}")
        print(f"  Current working directory: {os.getcwd()}")
        print(f"  Project root directory: {project_root}")
        exit(1)

    # once confirmed that it exists and we're good to continue
    print("\n" + "="*50)
    print("Environment variables loaded")
    print("="*50)

    # test the variables in the .env file. If they exist and specified in the .env file then you get the deets belows
    # otherwise, default is "NOT SET"
    print(f"APP NAME = {os.getenv('APP_NAME', 'NOT SET')}")
    print(f"APP ENV = {os.getenv('APP_ENV', 'NOT SET')}")
    print(f"DATABASE = {os.getenv('DATABASE_URL', 'NOT SET')}")
    print(f"DEBUG = {os.getenv('DEBUG', 'NOT SET')}")
    print(f"PORT = {os.getenv('PORT', 'NOT SET')}")

    # check the more sensitive items in your .env file, check without printing the keys
    if os.getenv("OPENAI_API_KEY"):
        key = os.getenv("OPENAI_API_KEY")
        print(f"OPENAI_API_KEY = {key[:10]}... (hidden)")
        print(f"OPENAI_MODEL = {os.getenv('OPENAI_MODEL', 'NOT SET')}")
    else:
        print("OPENAI_API_KEY = NOT SET")

    if os.getenv("AWS_ACCESS_KEY_ID"):
        key = os.getenv("AWS_ACCESS_KEY_ID")
        print(f"AWS_ACCESS_KEY_ID = {key[:10]}... (hidden)")
    else:
        print("AWS_ACCESS_KEY_ID = NOT SET")

if __name__ == "__main__":
    test_env_loading()