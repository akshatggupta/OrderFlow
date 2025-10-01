# this is just a sample code to get familiar with nats

import os
import asyncio


import nats
from nats.errors import TimeoutError


servers = os.environ.get("NATS_URL", "nats://localhost:4222").split(",")


async def main():

    nc = await nats.connect(servers=servers)


    await nc.publish("greet.joe", b"hello")


    sub = await nc.subscribe("greet.*")


    try:
        msg = await sub.next_msg(timeout=0.1)
    except TimeoutError:
        pass


    await nc.publish("greet.joe", b"hello")
    await nc.publish("greet.pam", b"hello")


    msg = await sub.next_msg(timeout=0.1)
    print(f"{msg.data} on subject {msg.subject}")


    msg = await sub.next_msg(timeout=0.1)
    print(f"{msg.data} on subject {msg.subject}")


    await nc.publish("greet.bob", b"hello")


    msg = await sub.next_msg(timeout=0.1)
    print(f"{msg.data} on subject {msg.subject}")


    await sub.unsubscribe()
    await nc.drain()




if __name__ == '__main__':
    asyncio.run(main())