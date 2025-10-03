from service import service
import click
import sys


# Group commands
@click.group()
def cli():
    """OrderFlow CLI"""
    pass


# Register subcommands
cli.add_command(service)


if __name__ == "__main__":
    cli(args=sys.argv[1:])
