import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DERIBIT_CLIENT_ID")
api_secret = os.getenv("DERIBIT_CLIENT_SECRET")

username = api_key

DERIBIT_HOST = "fix-test.deribit.com"
DERIBIT_PORT = 9881
SOH = chr(1)

seq = 1