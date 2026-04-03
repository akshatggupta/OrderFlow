#!/usr/bin/env python3
import time
import base64
import hashlib
import socket
from config import *


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

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((DERIBIT_HOST, DERIBIT_PORT))


#auth

timestamp_in_ms = str(int(time.time())) + "000"
nonce64 = base64.b64encode(os.urandom(32)).decode()
raw_data = timestamp_in_ms + "." + nonce64

password = base64.b64encode(
    hashlib.sha256((raw_data + api_secret).encode()).digest()
).decode()

#logon
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

send_fix(s, logon_body)

data = s.recv(4096)
text = data.decode()

if "35=A" not in text:
    print("Logon failed:", text)
    exit(1)

print(" LOGON OK")

#MD request

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

send_fix(s, md_body)

print(" Listening...")

last_hb = time.time()

while True:
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
