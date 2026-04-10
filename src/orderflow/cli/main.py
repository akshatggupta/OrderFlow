import asyncio
import logging

from orderflow.fix_client import start_fix_client
from orderflow.parser.fix_parser import parse_raw
from orderflow.serializer.to_protobuf import to_protobuf
from orderflow.nats.publisher import NatsPublisher


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orderflow-main")


async def handle_fix_message(raw_msg: str, publisher: NatsPublisher):
    try:
        # 1. Parse FIX → dict
        parsed = parse_raw(raw_msg)
        logger.info("Parsed FIX message")

        # 2. Convert dict → protobuf bytes
        proto_bytes = to_protobuf(parsed)
        logger.info("Serialized to protobuf")

        # 3. Publish to NATS
        await publisher.publish("market.data.incremental", proto_bytes)
        logger.info("Published to NATS")

    except Exception as e:
        logger.error(f"Error processing message: {e}")



async def run():
    logger.info("Starting OrderFlow Pipeline...")

    # 1. Initialize NATS Publisher
    publisher = NatsPublisher()
    await publisher.connect()

    # 2. Start FIX client
    await start_fix_client(
        on_message=lambda msg: handle_fix_message(msg, publisher)
    )


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Shutting down...")