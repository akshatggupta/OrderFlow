import json
import nats


class NatsPublisher:
    def __init__(self):
        self.nc = None
        self.js = None

    async def connect(self):
        # connect to NATS
        self.nc = await nats.connect("nats://localhost:4222")
        self.js = self.nc.jetstream()

        # ensure stream exists
        try:
            await self.js.add_stream(
                name="MARKETDATA",
                subjects=["marketdata.>"]
            )
        except Exception:
            # stream already exists
            pass

    async def publish(self, subject: str, data: bytes):
        ack = await self.js.publish(subject, data)
        return ack

    def to_protobuf(self, data: dict) -> bytes:
        """
        TEMP: convert dict → JSON bytes
        (you can replace with real protobuf later)
        """
        return json.dumps(data).encode()