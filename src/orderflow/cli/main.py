import os
import sys
from pathlib import Path

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env in project root (3 levels up from this file)
    # OrderFlow/src/orderflow/cli/main.py -> OrderFlow/
    project_root = Path(__file__).parent.parent.parent.parent
    env_path = project_root / '.env'
    
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"✓ Loaded environment variables from {env_path}")
    else:
        print(f"⚠ No .env file found at {env_path}")
        print(f"  Searched in project root: {project_root}")
except ImportError:
    print("⚠ python-dotenv not installed, using system environment variables")

from service import start_fix_client


def main():
    """Main entry point for the Deribit FIX client"""
    
    print("\n" + "="*60)
    print("Deribit FIX Client")
    print("="*60 + "\n")
    
    # Get credentials from environment
    client_id = os.getenv("DERIBIT_CLIENT_ID")
    client_secret = os.getenv("DERIBIT_CLIENT_SECRET")
    
    # Validate credentials
    if not client_id or not client_secret:
        print(" ERROR: Missing credentials!\n")
        print("Please set the following environment variables:")
        print("  - DERIBIT_CLIENT_ID")
        print("  - DERIBIT_CLIENT_SECRET")
        print("\nYou can either:")
        print("  1. Create a .env file in the project root with:")
        print("     DERIBIT_CLIENT_ID=your_client_id")
        print("     DERIBIT_CLIENT_SECRET=your_client_secret")
        print("\n  2. Or export them in your terminal:")
        print("     export DERIBIT_CLIENT_ID=your_client_id")
        print("     export DERIBIT_CLIENT_SECRET=your_client_secret")
        sys.exit(1)
    
    # Config file path (you can change this if needed)
    config_file = "initiator.cfg"
    
    if not Path(config_file).exists():
        print(f"❌ ERROR: Config file '{config_file}' not found!")
        print(f"Please ensure {config_file} exists in the current directory.")
        sys.exit(1)
    
    print(f"✓ Client ID: {client_id[:8]}..." if len(client_id) > 8 else f"✓ Client ID: {client_id}")
    print(f"✓ Config file: {config_file}")
    print()
    
    # Start the FIX client
    start_fix_client(client_id, client_secret, config_file)


if __name__ == "__main__":
    main()