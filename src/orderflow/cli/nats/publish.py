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
            subjects = ["marketdata.>"]

        )
    except nats.js.errors.BadRequestError:
        pass
    
    symbol = envelope.symbol  #tag 55 of fix
    subject = f"marketdata.{symbol}"
    proto_bytes = envelope.SerialzeToString()
    ack = await js.publish(
        subject,
        proto_bytes,
    )

    print(f"stored in stream={ack.stream} at seq={ack.seq}")


    await nc.drain()


asyncio.run(main())
    

