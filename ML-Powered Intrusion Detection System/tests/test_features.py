from app.features import apply_inference_engineering, encode_protocol

FLOW = {"src_ip": "1.2.3.4", "dst_ip": "10.0.0.1", "src_port": 1234, "dst_port": 443,
        "proto": "tcp", "duration": 1.2, "src_bytes": 100, "dst_bytes": 0,
        "conn_state": "SF", "src_pkts": 4, "dst_pkts": 0}


def test_protocol_mapping():
    assert encode_protocol("tcp") == 1
    assert encode_protocol("udp") == 2
    assert encode_protocol("icmp") == 3
    assert encode_protocol("weird") == 0


def test_engineering_outputs_numeric_with_ratios_and_onehot():
    df = apply_inference_engineering(FLOW)
    assert df["byte_ratio"].iloc[0] == 100
    assert df["conn_state_SF"].iloc[0] == 1
    assert df["conn_state_S0"].iloc[0] == 0
    assert not df.isna().any().any()
