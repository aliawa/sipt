

send(invite) => [$server.addr]
    INVITE sip:1024@[$server.ip] SIP/2.0
    Via: SIP/2.0/UDP [$local.addr];branch=z9hG4bK-[$tag]
    To: <sip:1024@[$server.addr]>
    From: <sip:1024@[$server.addr]>;tag=1
    Contact: <sip:1024@[$local.addr]>;transport=UDP
    Expires: 3600
    User-agent: sipt-ua
    Call-ID: [$tag]@[$local.ip]
    CSeq: 1 REGISTER
    Content-Type: application/sdp
    Content-Length: [$len]

    v=0
    o=user1 53655765 2353687637 IN IP[$local.ver] [$local.ip]
    s=-
    c=IN IP[$local.ver] [$local.ip]
    t=0 0
    m=audio [$local.audioport] RTP/AVP 0 8 18 101
    a=rtpmap:0 PCMU/8000
    a=rtpmap:8 PCMA/8000
    a=rtpmap:18 G729/8000
    a=rtpmap:101 telephone-event/800

recv(okay):
