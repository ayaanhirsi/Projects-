"""Inference-time feature engineering. Must mirror what was done during training."""
import json
import os
import pandas as pd

from app.config import FEATURE_COLUMNS_PATH

PROTO_MAP = {"tcp": 1, "udp": 2, "icmp": 3}
DEFAULT_PROTO_CODE = 0  # unknown protocols still flow through the pipeline

CONN_STATES = ["S0", "S1", "S2", "S3", "SF", "REJ", "RSTO", "RSTR",
               "RSTOS0", "RSTRH", "SH", "SHR", "OTH"]

DROP_COLS = ["src_ip", "dst_ip", "proto", "conn_state"]


def encode_protocol(proto: str) -> int:
    return PROTO_MAP.get(str(proto).lower(), DEFAULT_PROTO_CODE)


def apply_inference_engineering(flow: dict) -> pd.DataFrame:
    """Turn one raw flow dict into the numeric feature row the models expect."""
    df = pd.DataFrame([flow])

    df["proto_code"] = df["proto"].map(encode_protocol)

    # Ratio features (+1 avoids division by zero)
    df["byte_ratio"] = df["src_bytes"] / (df["dst_bytes"] + 1)
    df["pkt_ratio"] = df["src_pkts"] / (df["dst_pkts"] + 1)

    # One-hot connection states: conn_state_S0, conn_state_SF, conn_state_REJ, ...
    for state in CONN_STATES:
        df[f"conn_state_{state}"] = (df["conn_state"] == state).astype(int)

    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns])

    # Cast to numeric; missing/invalid -> 0 so no NaNs reach the models
    df = df.apply(pd.to_numeric, errors="coerce").fillna(0)

    # Align columns to the exact training order if a column list is shipped with the models
    if os.path.exists(FEATURE_COLUMNS_PATH):
        with open(FEATURE_COLUMNS_PATH) as f:
            df = df.reindex(columns=json.load(f), fill_value=0)

    return df
