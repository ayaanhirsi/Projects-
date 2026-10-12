"""Pydantic schema that validates every incoming network flow (422 on bad input)."""
from typing import List, Optional
from pydantic import BaseModel, Field


class FlowData(BaseModel):
    src_ip: str
    dst_ip: str
    src_port: int = Field(ge=0, le=65535)
    dst_port: int = Field(ge=0, le=65535)
    proto: str
    duration: float = Field(ge=0)
    src_bytes: int = Field(ge=0)
    dst_bytes: int = Field(ge=0)
    conn_state: str
    missed_bytes: int = Field(default=0, ge=0)
    src_pkts: int = Field(ge=0)
    src_ip_bytes: int = Field(default=0, ge=0)
    dst_pkts: int = Field(ge=0)
    dst_ip_bytes: int = Field(default=0, ge=0)

    # Optional DNS / HTTP fields
    dns_qclass: Optional[int] = 0
    dns_qtype: Optional[int] = 0
    dns_rcode: Optional[int] = 0
    http_request_body_len: Optional[int] = 0
    http_response_body_len: Optional[int] = 0
    http_status_code: Optional[int] = 0


class BatchRequest(BaseModel):
    flows: List[dict]
