recv(register):
    REGISTER.*


send(okay) => [$register.via.addr]
    SIP/2.0 200 OK
    [register.via]
    [register.from]
    [register.To];tag=[tag]
    [register.from]
    [register.call-id]
    [register.cseq]
    [register.contact]
    Expires: 3600

