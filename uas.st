recv(register):
    REGISTER.*


send(okay) => [$register.via.addr]
    SIP/2.0 200 OK
    Via: [$register.via]
    From: [$register.from]
    To: [$register.to];tag=[$tag]
    Call-Id: [$register.call-id]
    CSeq: [$register.cseq]
    Contact: [$register.contact]
    Expires: 3600
    Content-Length: 0

