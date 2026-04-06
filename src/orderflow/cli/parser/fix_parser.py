from __future__ import annotations

import sys
import os
from orderflow.cli.raw_fix_client import *
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))



from datetime import datetime,timezone
from typing import Any

TAG={
    "8":  "begin_string",
    "9":  "body_length",
    "35": "msg_type",
    "49": "sender_comp_id",
    "56": "target_comp_id",
    "34": "msg_id",
    "52": "sending_time",
    "55": "symbol",
    "231": "contract_multiplier",
    "746": "open_intrest",
    "262": "md_req_id",
    "268": "no_md_entries",
    "279": "md_update_action",
    "269": "md_entry_type",
    "270": "md_entry_px",
    "271": "md_entry_size",
    "272": "md_entry_date",
    "10": "checksum",

    "100087": "deribit_instrument_id",
    "100090": "deribit_market_price",

}

MD_GROUP_TAG = {"279","269","270","271","272"}

GROUP_START_TAG = "279"

def fix_time_to_epoch(ts:str) -> int:
    try:
        dt = datetime.strptime(ts, "%Y%m%d-%H:%M:%S.%f").replace(tzinfo=timezone.utc)
    except ValueError:
        dt = datetime.strptime(ts, "%Y%m%d-%H:%M%S").replace(tzinfo = timzone.utc)
    return int(dt.timestamp())*1000

def fix_time_to_epoch_us(ts:str) -> int:
    return fix_time_to_epoch(ts)*1000


def parse_raw(data:bytes) -> dict[str,Any]:
    raw = data.decode("ascii", errors = "replace") if isinstance(data,bytes) else data

    fields: dict[str,Any] = {}
    md_entries : list[dict] = []
    current_entry : dict | None = None
    in_group = False

    for pair in raw.split("\x01"):
        if "=" not in pair:
            continue
        tag,value = pair.split("=", 1)

        if tag == "268":
            in_group = True
            fields["no_md_entries"] = int(value)
            continue 
        if in_group and tag in MD_GROUP_TAG:
            if tag == GROUP_START_TAG:
                if current_entry:
                    md_entries.append(current_entry)
                current_entry = {}
                if current_entry is not None:
                    current_entry[TAG.get(tag, f"tag_{tag}")] = _coerce(tag,value)
            
        name = TAG.get(tag, f"tag_{tag}")
        fields[name] = _coerce(tag,value)   
        
    if current_entry:
        md_entries.append(current_entry)

    if md_entries:
        fields["md_entries"] = md_entries
    
    print(fields)



def _coerce(tag: str, value: str) -> Any:
    """Type-coerce FIX field values.
        Because we are converting the bits into the str first after 
        that we cant store the tag value are string there are float and int value"""


    int_tags  = {"9", "34", "268", "279", "269", "10", "100087"}
    float_tags = {"270", "271", "231", "746", "100090"}
    time_tags  = {"52", "272"}
 
    if tag in int_tags:
        return int(value)
    if tag in float_tags:
        return float(value)
    if tag in time_tags:
        return value  
    return value