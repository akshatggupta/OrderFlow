import asyncio
import logging
import subprocess
import time
import sys
import click
from orderflow.cli.raw_fix_client import start_fix_client
from orderflow.cli.nats.publish import NatsPublisher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s"
)
logger = logging.getLogger("orderflow")


async def handle_fix_message(parsed: dict, publisher: NatsPublisher):
    """
    Publish an already-parsed FIX message to NATS as protobuf.

    `parsed` is produced once by raw_fix_client.start_fix_client() and handed
    to this callback -- do NOT call parse_raw() again here. Re-parsing would
    double the CPU cost per message and risks divergence if the two parse
    paths ever disagree.
    """
    try:
        msg_type = parsed.get("msg_type", "?")
        seq      = parsed.get("msg_seq_num", "?")

        # Skip empty refreshes -- nothing to publish. Applies to both
        # incremental (X) and snapshot (W) messages: a snapshot with no
        # entries is as useless downstream as an incremental with none.
        if not parsed.get("md_entries"):
            logger.debug(f"Empty refresh seq={seq} type={msg_type} — skipping")
            return

        # Serialize dict → protobuf bytes
        proto_bytes = publisher.to_protobuf(parsed)

        # Publish to NATS JetStream
        symbol  = parsed.get("symbol", "UNKNOWN")
        subject = f"marketdata.{symbol}"
        ack     = await publisher.publish(subject, proto_bytes)

        logger.info(
            f"Published | seq={seq} type={msg_type} "
            f"symbol={symbol} entries={len(parsed.get('md_entries', []))} "
            f"stream_seq={ack.seq} bytes={len(proto_bytes)}"
        )

    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)


async def run_pipeline(config: str):
    """Main async pipeline — connects NATS then starts FIX client."""
    logger.info("Starting OrderFlow pipeline...")

    # connect to NATS and set up stream
    publisher = NatsPublisher()
    await publisher.connect()
    logger.info("NATS connected")

    # 2. start FIX client — passes each already-parsed message to
    # handle_fix_message. start_fix_client() calls parse_raw() exactly once
    # per message and forwards (msg, parsed) here, so this callback must
    # accept both positional args even though only `parsed` is used.
    logger.info(f"Starting FIX client with config: {config}")
    await start_fix_client(
        config=config,
        on_message=lambda msg, parsed: asyncio.create_task(
            handle_fix_message(parsed, publisher)
        )
    )


@click.group()
def cli():
    """OrderFlow — FIX → Protobuf → NATS pipeline"""
    pass


@cli.command()
@click.option(
    "--config",
    default="src/orderflow/cli/config/initiator.cfg",
    show_default=True,
    help="Path to FIX initiator config"
)
def service(config):
    """Start FIX client + NATS publisher pipeline."""
    try:
        asyncio.run(run_pipeline(config))
    except KeyboardInterrupt:
        logger.info("Shutting down pipeline...")


@cli.command()
def infra():
    """Start NATS via docker-compose."""
    click.echo("Starting NATS...")
    result = subprocess.run(
        ["docker-compose", "up", "-d"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        click.echo(f"Failed to start NATS:\n{result.stderr}", err=True)
        sys.exit(1)

    # wait for health check
    click.echo("Waiting for NATS to be healthy...")
    for i in range(10):
        time.sleep(2)
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:8222/healthz", timeout=2)
            click.echo(" NATS is ready")
            return
        except Exception:
            click.echo(f"  still waiting... ({(i+1)*2}s)")

    click.echo("  NATS may not be ready — check docker-compose logs", err=True)


@cli.command()
@click.option(
    "--config",
    default="src/orderflow/cli/config/initiator.cfg",
    show_default=True,
    help="Path to FIX initiator config"
)
@click.pass_context
def start(ctx, config):
    """
    Single command — starts NATS infra + full pipeline.

    Usage:
        python3 -m orderflow.cli.main start
        task start
    """
    # 1. start NATS
    ctx.invoke(infra)

    # 2. start pipeline
    click.echo("Starting FIX → NATS pipeline...")
    ctx.invoke(service, config=config)


@cli.command()
def stop():
    """Stop NATS docker-compose services."""
    click.echo("Stopping NATS...")
    subprocess.run(["docker-compose", "down"])
    click.echo(" NATS stopped")


@cli.command()
def status():
    """Check NATS JetStream status."""
    try:
        import urllib.request, json
        with urllib.request.urlopen("http://localhost:8222/jsz") as r:
            data = json.loads(r.read())
        click.echo(f" NATS JetStream is running")
        click.echo(f"   streams   = {data.get('streams', 0)}")
        click.echo(f"   messages  = {data.get('messages', 0)}")
        click.echo(f"   bytes     = {data.get('bytes', 0)}")
        click.echo(f"   consumers = {data.get('consumers', 0)}")
    except Exception as e:
        click.echo(f"❌ NATS not reachable: {e}", err=True)


if __name__ == "__main__":
    cli()