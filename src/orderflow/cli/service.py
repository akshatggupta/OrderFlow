import click
import logging
import asyncio
import websockets
import json
import quickfix as fix
import quickfix44 as fix44
import time
import logging
import hashlib
import base64
import os
from datetime import datetime


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class DeribitFIXApplication(fix.Application): 
    def __init__(self, client_id, client_secret):
        super().__init__()   
        self.client_id = client_id
        self.client_secret = client_secret
        self.session_id = None
        self.logged_on = False

    def onCreate(self, sessionID):
        """ Calls when iniatlizing the fix connection """
        logger.info(f"session is created {sessionID}")  # shows the session id not neccessary but lowkey still using 
        self.session_id = sessionID

    def onLogon(self, sessionID):
        """ calls when successfull login occurs (deribit checks) """
        logger.info(f"a succesfull logon occur{sessionID}")  # no need but its looks good on terminal
        self.logged_on = True
        self.subscribe_market_data(sessionID)

    def onLogout(self, sessionID):
        logger.info(f"connection stops on this id{sessionID}")
        self.logged_on = False

    def toAdmin(self, message, sessionID):
        """ Message authentication handle here """
        msg_type = fix.MsgType()
        message.getHeader().getField(msg_type)

        nonce = os.urandom(32)

        timestamp_ms = str(int(time.time() * 1000))  #

        nonce_b64 = base64.b64encode(nonce).decode('utf-8')
        raw_data = f"{timestamp_ms}.{nonce_b64}"

        # Calculate signature = base64(SHA256(raw_data + client_secret))
        signature_input = raw_data + self.client_secret
        signature_hash = hashlib.sha256(signature_input.encode('utf-8')).digest()
        signature_b64 = base64.b64encode(signature_hash).decode('utf-8')
            
        message.setField(fix.Username(self.client_id))              # tag 553
        message.setField(fix.Password(signature_b64))               # tag 554
        message.setField(fix.RawData(raw_data))                     # tag 96
        message.setField(fix.RawDataLength(len(raw_data)))          # tag 95

        logger.info("Sending Logon with Deribit authentication")
        logger.debug(f"  Timestamp: {timestamp_ms}")
        logger.debug(f"  RawData: {raw_data}")

    def fromAdmin(self, message, sessionID):
        """ call when incoming message deribit-->quickfix usually tells the deribit that i recieved the message """
        msg_type = fix.MsgType()
        message.getHeader().getField(msg_type)

        if msg_type.getValue() == fix.MsgType_Logon:
            logger.info(f"recieved logon")

        elif msg_type.getValue() == fix.MsgType_Logout:
            text = fix.Text()
            if message.isSetField(text):
                message.getField(text)
                logger.warning(f"logout for the reason {text.getValue()}")
        elif msg_type.getValue() == fix.MsgType_Reject:
            logger.error(f"Received Reject: {message}")
        else:
            logger.debug(f"Admin message: {msg_type.getValue()}")

    def toApp(self, message, sessionID):
        """ call for the outgoing msg """
        logger.debug(f"sending message to app {message}")

    def fromApp(self, message, sessionID):
        """ call from incoming msg """
        try:
            self.process_message(message, sessionID)
        except Exception as e:
            logger.error(f"error msg: {e}", exc_info=True)

    def process_message(self, message, sessionID):
        """ process the incoming message coming from deribit """

        msg_type = fix.MsgType()
        message.getHeader().getField(msg_type)

        if msg_type.getValue() == fix.MsgType_MarketDataSnapshotFullRefresh:
            self.handle_marketdata_snapshot(message)
        elif msg_type.getValue() == fix.MsgType_MarketDataIncrementalRefresh:
            self.handle_marketdata_incremental(message)
        elif msg_type.getValue() == fix.MsgType_MarketDataRequestReject:
            self.handle_market_data_reject(message)
        else:
            logger.debug(f"recived msg type: {msg_type.getValue()}")

    def handle_marketdata_snapshot(self, message):
        """ handle market data snapshot {W} """
        symbol = fix.Symbol()
        message.getField(symbol)
        logger.info(f"Market data snapshot {symbol.getValue()}")

        no_md_entries = fix.NoMDEntries()  # repeating group(specifies the no of entry) as given in deribit fix doc
        message.getField(no_md_entries)

        group = fix44.MarketDataSnapshotFullRefresh.NoMDEntries()

        bids = []
        asks = []
        trades = []

        for i in range(1, no_md_entries.getValue() + 1):
            message.getGroup(i, group)
            md_entry_type = fix.MDEntryType()
            group.getField(md_entry_type)

            md_entry_px = fix.MDEntryPx()
            md_entry_size = fix.MDEntrySize()
            group.getField(md_entry_px)
            group.getField(md_entry_size)

            entry_type = md_entry_type.getValue()
            price = md_entry_px.getValue()
            size = md_entry_size.getValue()

            if entry_type == '0':  # when bid
                bids.append((price, size))
            elif entry_type == '1':  # when ask
                asks.append((price, size))
            elif entry_type == '2':  # when trade
                trades.append((price, size))

        if bids:
            logger.info(f"info for top 5 bids")
            for price, size in bids[:5]:
                logger.info(f"{price}||{size}")
        if asks:
            logger.info(f"info for top 5 asks")
            for price, size in asks[:5]:
                logger.info(f"{price}||{size}")

        if trades:
            logger.info(f"info for trades")
            for price, size in trades[:5]:
                logger.info(f"{price}||{size}")

    def handle_marketdata_incremental(self, message):
        """ handle market incremental data (X) symbol """

        no_md_entries = fix.NoMDEntries()
        message.getField(no_md_entries)

        group = fix44.MarketDataIncrementalRefresh.NoMDEntries()

        for i in range(1, no_md_entries.getValue() + 1):
            message.getGroup(i, group)
            md_update_action = fix.MDUpdateAction()
            md_entry_type = fix.MDEntryType()
            md_entry_px = fix.MDEntryPx()
            md_entry_size = fix.MDEntrySize()
            symbol = fix.Symbol()

            group.getField(md_update_action)
            group.getField(md_entry_type)
            group.getField(symbol)
            group.getField(md_entry_px)

            size = 0
            if group.isSetField(md_entry_size):
                group.getField(md_entry_size)
                size = md_entry_size.getValue()
            
            action = md_update_action.getValue()
            entry_type = md_entry_type.getValue()
            
            logger.info(f"Update: {symbol.getValue()} | "
                       f"Action: {action} | Type: {entry_type} | "
                       f"Price: {md_entry_px.getValue()}")

    def handle_market_data_reject(self, message):
        """Handle market data request rejection (Y)"""
        md_req_id = fix.MDReqID()
        text = fix.Text()
        
        message.getField(md_req_id)
        if message.isSetField(text):
            message.getField(text)
            logger.error(f"Market Data Request Rejected - ID: {md_req_id.getValue()}, "
                        f"Reason: {text.getValue()}")
        else:
            logger.error(f"Market Data Request Rejected - ID: {md_req_id.getValue()}")

    def subscribe_market_data(self, sessionID):
        message = fix44.MarketDataRequest()
        req_id = f"MD_{int(time.time())}"
        message.setField(fix.MDReqID(req_id))

        message.setField(fix.SubscriptionRequestType('1'))  # here 1 is snapshot+update
        message.setField(fix.MarketDepth(10)) 
        message.setField(fix.MDUpdateType(1))

        instruments = ["BTC-PERPETUAL"]  # for now taking btc

        for instrument in instruments:
            group = fix44.MarketDataRequest.NoRelatedSym()
            group.setField(fix.Symbol(instrument))
            message.addGroup(group)

        logger.info(f"Request id {req_id}")

        entry_types = ['0', '1', '2']

        for entry_type in entry_types:
            group = fix44.MarketDataRequest.NoMDEntryTypes()
            group.setField(fix.MDEntryType(entry_type))
            message.addGroup(group)

        logger.info(f"Request id:{req_id}")

        fix.Session.sendToTarget(message, sessionID)

    def unsubscribe_market_data(self, sessionID, md_req_id):
        """ unsubscribing the market data """

        message = fix44.MarketDataRequest()
        message.setField(fix.MDReqID(md_req_id))
        message.setField(fix.SubscriptionRequestType('2'))

        logger.info(f"Unsubscribing to the market data {md_req_id}")

        fix.Session.sendToTarget(message, sessionID)


def start_fix_client(client_id, client_secret, config_file="initiator.cfg"):
    """Start the FIX client with given credentials"""

    logger.info("\n" + "="*60)
    logger.info("Deribit FIX Client Starting")
    logger.info("="*60 + "\n")

    
    config_file = str(config_file)

    application = DeribitFIXApplication(client_id, client_secret)

    
    settings = fix.SessionSettings(config_file)

    store_factory = fix.FileStoreFactory(settings)

   
    initiator = fix.SocketInitiator(application, store_factory, settings)

    initiator.start()
    logger.info("Connecting to Deribit FIX API...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n" + "="*60)
        logger.info("Shutting down gracefully...")
        logger.info("="*60)
    finally:
        initiator.stop()


# Config load

if __name__ == "__main__":
    client_id = os.getenv("DERIBIT_CLIENT_ID")
    client_secret = os.getenv("DERIBIT_CLIENT_SECRET")
    start_fix_client(client_id, client_secret, "initiator.cfg")
