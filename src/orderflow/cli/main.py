import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent.parent.parent
    env_path = project_root / '.env'
    
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f" Loaded environment variables from {env_path}")
    else:
        print(f" No .env file found at {env_path}")
        print(f"  Searched in project root: {project_root}")
except ImportError:
    print("⚠ python-dotenv not installed, using system environment variables")

from service import start_fix_client


def main():
    """Main entry point for the Deribit FIX client"""

if __name__ == "__main__":
    main()