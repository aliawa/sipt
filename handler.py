from collections import namedtuple
from ipaddress import ip_address
import socket
import string
import random
import re

# vars 
# local.ip   local.port   local.addr
# remote.ip  remote.port  remote.addr
# <msg>.<header>


IPAddr = namedtuple("IPAddr", "addr version")

def addr_to_str(ipaddr, bPort):
    if bPort and ipaddr.addr[1] != 5060:
        if addr.version == 6:
            strAddr = "[{1}]:{2}".format(ipaddr.addr[0], ipaddr.addr[1])
        else:
            strAddr = "{1}:{2}".format(ipaddr.addr[0], ipaddr.addr[1])
        return strAddr
    else:
        return ipaddr.addr[0]


def parseIP(ipstr):
    ip, separator, port = ipstr.rpartition(':')
    print "ip=",ip, "port=",port, "separator=",separator
    assert separator # separator (`:`) must be present
    port = int(port) # convert to integer
    ip = ip_address(unicode(ip.strip("[]"))) # convert to `IPv4Address` or `IPv6Address` 
    return IPAddr(addr=(str(ip), port), version=ip.version)


class Handler:
    # Actions
    NONE = 0
    SEND = 1
    RECV = 2

    # Destinations
    NODST  = 0

    def __init__(self, scenario, srvr_addr, clnt_addr, contxt):
        self.scenario = scenario
        self.srvr_addr = srvr_addr
        self.clnt_addr = clnt_addr
        self.contxt = contxt
        
        self.messages = {}
        self.srvr_sock = self.getSock(srvr_addr[0], srvr_addr.version, "UDP")
        self.clnt_sock = self.getSock(clnt_addr[0], clnt_addr.version, "UDP")
        self.tagval = str(random.randint(1111,9999))

        print "Listning on : {0}:{1}".format( srvr_addr.addr[0], srvr_addr.addr[1])
        print "Sending from: {0}:{1}".format( clnt_addr.addr[0], clnt_addr.addr[1])
        print


    def getSock(self, addr, version , transport):
        if version == 6:
            family= socket.AF_INET6
        else:
            family= socket.AF_INET

        if transport == "UDP":
            typ = socket.SOCK_DGRAM
        else:
            typ = socket.SOCK_STREAM

        sock = socket.socket(family,typ)
        if addr[1]:
            sock.bind(addr)

        return sock



    def msg_getValueStr(self, name, val, var):
        if name == 'via':
            l = re.split('\s|;', val)
            if var[0] == 'addr':
                return addr_to_str(parseIP(l[1]),True)
        return ''



    def getValueStr(self, var):
        var_seq = string.split(var, '.')
        if var_seq[0] == 'local':
            if var_seq[1] == 'ip':
                return self.srvr_addr.addr[0]
            elif var_seq[1] == 'port':
                return str(self.srvr_addr.addr[1])
            elif var_seq[1] == 'addr':
                return addr_to_str(self.srvr_addr, True)

        elif var_seq[0] == 'server':
            if var_seq[1] == 'ip':
                return self.contxt['remote'].addr[0]
            elif var_seq[1] == 'port':
                return str(self.contxt['remote'].addr[1])
            elif var_seq[1] == 'addr':
                return addr_to_str(self.contxt['remote'] ,True)

        elif var_seq[0] == 'tag':
            return self.tagval

        elif self.messages.has_key(var_seq[0]):
            if len(var_seq) == 2:
                # The entire header
                return self.messages[var_seq[0]][var_seq[1]]
            else:
                return msg_getValueStr(var_seq[1], 
                        self.messages[var_seq[0]][var_seq[1]], var_seq[2:])
        else:
            print "unknown variable", var
            return ''



    def getValue(self, var):
        var_seq = string.split(var, '.')

        if var_seq[0] == 'server':
            if var_seq[1] == 'addr':
                return self.contxt['remote'].addr



    def populate(self, msg, dst):
        msg_lst = re.split('\[|\]', msg)
        for i, item in enumerate(msg_lst):
            if item[0] == '$':
                msg_lst[i] = self.getValueStr(item[1:])
        return ''.join(msg_lst)



    def save_msg(self, name, msg, src=''):
        print "saving:", name
        msg_lst = msg.split('\r\n')
        msg_dct = {}
        msg_dct['first'] = msg_lst[0]
        for item in msg_lst[1:]:
            l = item.split(':',1)
            key = string.lower(l[0].strip())
            if key:
                msg_dct[key] = l[1].strip()
        if src:
            msg_dct['src'] = src

        self.messages[name] = msg_dct



    def send(self, data, dest):
        if dest == '': # dest not given -> use remote
            addr = self.context['remote']
        elif dest[0] == '$':
            addr = self.getValue(dest[1:])
        else:
            addr = parseIP(dest).addr

        print "sending to", addr
        req = self.populate(data, addr)
        print req

        self.clnt_sock.sendto(req, addr);
        return req



    def recv(self, match):
        data, addr = self.srvr_sock.recvfrom(1024)
        print "received from", addr, "\n", data
        print
        return data, addr;



    def execute(self):
        for a in self.scenario:
            if a['action'] == self.SEND:
                print "executing send:"
                msg = self.send(a['data'], a['dest'])
                self.save_msg(a['name'], msg)
            elif a['action'] == self.RECV:
                print "executing recv:"
                dt = ''
                if a.has_key('data'):
                    dt = a['data']
                msg, addr = self.recv(dt)
                self.save_msg(a['name'], msg, src=addr)
            else:
                print "unknow action", a['action']

