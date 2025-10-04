import click
import logging
import asyncio
import websockets
import json

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@click.command()
def service():
    """Runs the main service."""
    
    msg = {
        "id": 7358,
        "jsonrpc": "2.0",
        "method": "public/get_currencies",
        "params": {}
    }

    async def call_api(msg):
        async with websockets.connect('wss://test.deribit.com/ws/api/v2') as websocket:
            await websocket.send(msg)
            while True:
                response = await websocket.recv() 
                data = json.loads(response)
                new_string=json.dumps(data, indent=2) #command to convert the json in python dict
                for item in data["result"]:
                    print(f"Currency: {item['currency']}, Network Fee: {item['network_fee']}")


    asyncio.get_event_loop().run_until_complete(call_api(json.dumps(msg)))

    # Init logger
    logger.info("This is info from logger")

    # Config load
if __name__ == "__main__":
    service()       