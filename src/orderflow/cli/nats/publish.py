import os
import asyncio

import nats
from nats.errors import TimeoutError

async def main():
    #connect to nats
    nc = await nats.connect("nats://localhost:4222")

    js = nc.jetstream()

    try:
        await js.add_stream(
            name = "MARKETDATA",
            subject = ["marketdata.>"]

        )
    except nats.js.errors.BadRequestError:
        pass

    proto_bytes = envelope.SerialzeToString()
    ack = await js.publish(
        "marketdata.BTC-PERCEPTUAL",
        proto_byte,
    )

    print(f"stored in stream={ack.stream} at seq={ack.seq}")


    await nc.drain()


asyncio.run(main())
    

