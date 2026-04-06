#!/usr/bin/env python3
import time
import base64
import hashlib
import socket
from orderflow.cli.config.config import *
from orderflow.cli.parser.fix_parser import parse_raw



def send_fix(sock, body):
    global seq

    body = body.replace("34=SEQ", f"34={seq}")
    seq += 1

    buff = "8=FIX.4.4" + SOH + "9=" + str(len(body)) + SOH + body

    checksum = 0
    for i in range(1, len(body)):
        checksum += ord(body[i])

    checksum = str(checksum % 256).zfill(3)
    buff += "10=" + checksum + SOH

    sock.sendall(buff.encode())

#connect

def connect(DERIBIT_HOST,DERIBIT_PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((DERIBIT_HOST, DERIBIT_PORT))
    return s


#auth
def auth(api_secret):
    timestamp_in_ms = str(int(time.time())) + "000"
    nonce64 = base64.b64encode(os.urandom(32)).decode()
    raw_data = timestamp_in_ms + "." + nonce64

    password = base64.b64encode(
        hashlib.sha256((raw_data + api_secret).encode()).digest()
    ).decode()
    return raw_data,password

#logon
def send_logon(sock,raw_data,password):
    logon_body = (
        "35=A" + SOH +
        "49=" + username + SOH +
        "56=DERIBITSERVER" + SOH +
        "34=SEQ" + SOH +
        "52=" + str(time.time()) + SOH +
        "98=0" + SOH +
        "108=30" + SOH +
        "95=" + str(len(raw_data)) + SOH +
        "96=" + raw_data + SOH +
        "553=" + username + SOH +
        "554=" + password + SOH
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
        "49=" + username + SOH +
        "56=DERIBITSERVER" + SOH +
        "34=SEQ" + SOH +
        "52=" + str(time.time()) + SOH +
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
        "269=2" + SOH +
        "269=1" + SOH
    )

    send_fix(sock, md_body)

    print(" Listening...")

def heartbeat(sock):
    body = (
        "35=0" + SOH +
        f"49={username}" + SOH +
        "56 = DERIBITSERVER" + SOH +
        "36 = seq" + SOH +
        "52 = {time.time()}" + SOH
    )
    send_fix(sock,body)

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


def main():
    sock = connect(DERIBIT_HOST, DERIBIT_PORT)

    raw_data, password = auth(api_secret)

    send_logon(sock, raw_data, password)
    send_market_data_req(sock)

    print(" Listening for data...")

    last_hb = time.time()
    buffer = b""

    while True:
        data = sock.recv(4096)

        if not data:
            continue

        buffer += data

        messages, buffer = extract_messages(buffer)

        print(f" Extracted {len(messages)} messages")

        for msg in messages:
            parsed = parse_raw(msg)
            print(" PARSED:", parsed)

if __name__ == "__main__":
    main()

"""while True:
    if time.time() - last_hb > 25:
        hb = (
            "35=0" + SOH +
            "49=" + username + SOH +
            "56=DERIBITSERVER" + SOH +
            "34=SEQ" + SOH +
            "52=" + str(time.time()) + SOH
        )
        send_fix(s, hb)
        last_hb = time.time()

    data = s.recv(4096)
    if data:
        print(data)
"""