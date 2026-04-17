#!/usr/bin/env python3
import time
import base64
import hashlib
import os
import socket
import asyncio
from datetime import datetime, timezone
from orderflow.cli.parser.fix_parser import parse_raw
from orderflow.cli.config.config import (
    DERIBIT_HOST,
    DERIBIT_PORT,
    SOH,
    seq,
    username,
    api_secret,
)


def fix_timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]


def send_fix(sock, body):
    global seq

    body = body.replace("34=SEQ", f"34={seq}")
    seq += 1

    body_bytes = body.encode()
    header = f"8=FIX.4.4{SOH}9={len(body_bytes)}{SOH}"

    msg = header.encode() + body_bytes

    checksum = sum(msg) % 256
    msg += f"10={str(checksum).zfill(3)}{SOH}".encode()

    sock.sendall(msg)

#connect

def connect(DERIBIT_HOST,DERIBIT_PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((DERIBIT_HOST, DERIBIT_PORT))
    return s


#auth
def auth(api_secret):
    timestamp = str(int(time.time() * 1000))   
    nonce64 = base64.b64encode(os.urandom(32)).decode()
    raw_data = f"{timestamp}.{nonce64}"

    password = base64.b64encode(
        hashlib.sha256((raw_data + api_secret).encode()).digest()
    ).decode()
    return raw_data,password

#logon
def send_logon(sock,raw_data,password):
    logon_body = (
        "35=A" + SOH +
        f"49={username}" + SOH +
        "56=DERIBITSERVER" + SOH +
        f"34=SEQ" + SOH +
        f"52={fix_timestamp()}" + SOH +
        "98=0" + SOH +
        "108=30" + SOH +
        f"95={len(raw_data)}" + SOH +
        f"96={raw_data}" + SOH +
        f"553={username}" + SOH +    
        f"554={password}"+ SOH
    )

    send_fix(sock, logon_body)

    data = sock.recv(4096)
    text = data.decode()

    if "35=A" not in text:
        print("Logon failed:", text)
        exit(1)

    print(" LOGON OK")

#MD request
def send_market_data_req(sock):

    symbols = ["BTC-PERPETUAL", "ETH-PERPETUAL", "SOL_USDC-PERPETUAL"]

    md_body = (
        "35=V" + SOH +
        f"49={username}" + SOH +
        "56=DERIBITSERVER" + SOH +
        "34=SEQ" + SOH +
        f"52={fix_timestamp()}" + SOH +
        "262=REQ1" + SOH +
        "263=1" + SOH +
        "265=1" + SOH +
        "264=1" + SOH +
        f"146={len(symbols)}" + SOH
    )

    for sym in symbols:
        md_body += f"55={sym}" + SOH

    md_body += (
        "267=2" + SOH +
        "269=0" + SOH +
        "269=1" + SOH
    )

    send_fix(sock, md_body)

    print(" Listening...")

def heartbeat(sock):
    body = (
        f"35=0{SOH}"
        f"49={username}{SOH}"
        f"56=DERIBITSERVER{SOH}"
        f"34=SEQ{SOH}"
        f"52={fix_timestamp()}{SOH}"
    )
    send_fix(sock, body)

def extract_messages(buffer: bytes):
    messages = []

    while True:
        start = buffer.find(b"8=FIX")
        if start == -1:
            return messages, buffer

        end = buffer.find(b"\x0110=", start)
        if end == -1:
            return messages, buffer

        # include checksum + SOH
        if len(buffer) < end + 7:
            return messages, buffer

        msg_end = end + 7
        msg = buffer[start:msg_end]

        messages.append(msg)
        buffer = buffer[msg_end:]

async def start_fix_client(config: str, on_message=None):
    sock = connect(DERIBIT_HOST,DERIBIT_PORT)
    raw_data,password = auth(api_secret)

    send_logon(sock,raw_data,password)
    send_market_data_req(sock)

    print("Listening for the data....")

    last_hb = time.time()
    buffer = b""
    loop = asyncio.get_running_loop()

    while True:
        data = await loop.run_in_executor(None, sock.recv, 4096)

        if time.time() - last_hb > 25:
            heartbeat(sock)
            last_hb = time.time()
        
        if not data:
            continue

        buffer+=data
        messages,buffer = extract_messages(buffer)
        print(f"Extracted {len(messages)} messages")

        for msg in messages:
            parsed =parse_raw(msg)
            print("PARSED:",parsed)
            if on_message:
                await on_message(msg)


def main():
    import asyncio

    async def debug_handler(msg):
        parsed = parse_raw(msg)
        print("PARSED:", parsed)
    asyncio.run(start_fix_client(on_message=debug_handler))
    
if __name__ == "__main__":
    main()

