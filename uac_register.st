

send(register) => [$server.addr]
    REGISTER sip:[$server.ip] SIP/2.0
    Via: SIP/2.0/UDP [$local.addr];branch=z9hG4bK-[$tag]
    To: <sip:1024@[$server.addr]>
    From: <sip:1024@[$server.addr]>;tag=1
    Contact: <sip:1024@[$local.addr]>;transport=UDP
    Expires: 3600
    User-agent: sipt-ua
    Call-ID: [$tag]@[$local.ip]
    CSeq: 1 REGISTER
    Content-Length: 0


recv(okay):
