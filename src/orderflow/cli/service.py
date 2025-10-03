import click
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@click.command()
def service():
    """Runs the main service."""

    # Init logger

    logger.info("This is info from logger")

    # Config load
