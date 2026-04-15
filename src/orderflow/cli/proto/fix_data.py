import fix_data_pb2 as pb 
from fix_parser import parse_raw, fix_time_to_epoch, fix_time_to_epoch_us


def to_protobuf(parsed:dict) -> bytes:

    header = pb.Header(
        begin_string = parsed["begin_string"],
        seq_num = parsed["msg_seq_num"],
        sender_comp_id = parsed["sender_comp_id"],
        target_comp_id = parsed["target_comp_id"],
        sending_time = fix_time_to_epoch_us(parsed["sending_time"])
    )

    instrument = pb.Instrument(
        symbol = parsed["symbol"],
        contract_multiplier = parsed["contract_multiplier"],
        instrument_id = parsed["deribit_instrument_id"],
        market_price = parsed["deribit_mark_price"],
        open_interest = parsed["open_interest"],
    )

    entries = []
    for e in parsed.get("md_entries",[]):
        entry = pb.MDEntry(
            update_action = e["md_update_action"],
            entry_type = e["md_entry_type"],
            price = e["md_entry_px"],
            size = e["md_entry_size"],
            entry_time_us = fix_time_to_epoch(e["md_entry_date"])
        )
    entries.append(entry)

    incremental = pb.MarketDataIncremental(
        header = header,
        instrument = instrument,
        md_req_id = parsed["md_req_id"],
        entries = entries 
    )


    incremental = pb.FIXEnvelope(
        msg_type = pb.MSG_TYPE_INCREMENTAL,
        incremental = incremental,
    )

    return envelope.SerializeToString()