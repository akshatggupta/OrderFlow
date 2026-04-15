async def main():
    nc = await nats.connect("nats://localhost:4222")
    js = nc.jetstream()

    # pull subscribe — you control fetch rate
    sub = await js.pull_subscribe(
        "marketdata.>",
        durable = "marketdata-consumer",
        stream="MARKETDATA"
    )

    while True:
        msgs = await sub.fetch(batch=10, timeout=1.0)  # fetch up to 10 at once
        for msg in msgs:
            envelope = pb.FIXEnvelope()
            envelope.ParseFromString(msg.data)
            # process it...
            await msg.ack()