

send(register) => [$server]
    REGISTER sip:[$server.ip] SIP/2.0
    Via: SIP/2.0/UDP [$local.ip]:[$local.port];branch=z9hG4bK-[$tag]
    To: <sip:1024@[$server.ip]:[$server.port]>
    From: <sip:1024@[$server.ip]:[$server.port]>;tag=1
    Contact: <sip:1024@[$local.ip]:[$local.port]>;transport=UDP
    Expires: 3600
    User-agent: sipt-ua
    Call-ID: [$tag]@[$local.ip]
    CSeq: 1 REGISTER
    Content-Length: 0


recv(okay):
