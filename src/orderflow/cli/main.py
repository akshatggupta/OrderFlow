from service import start_fix_client
import click
import sys
import os

# Load environment variables from .env file
from pathlib import Path
try:
    from dotenv import load_dotenv
    # Load .env from project root
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    # dotenv not installed, rely on system environment variables
    pass


@click.group()
def cli():
    """OrderFlow CLI"""
    pass


@click.command()
@click.option('--client-id', envvar='DERIBIT_CLIENT_ID', 
              help='Deribit Client ID')
@click.option('--client-secret', envvar='DERIBIT_CLIENT_SECRET',
              help='Deribit Client Secret')
@click.option('--config', default='initiator.cfg', 
              help='FIX config file')
def service(client_id, client_secret, config):
    """Start the Deribit FIX service"""
    
    if not client_id or not client_secret:
        click.echo("ERROR: Missing credentials!", err=True)
        click.echo("Set DERIBIT_CLIENT_ID and DERIBIT_CLIENT_SECRET environment variables")
        sys.exit(1)
    
    start_fix_client(client_id, client_secret, config)


cli.add_command(service)


if __name__ == "__main__":
    cli()