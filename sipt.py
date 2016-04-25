import socket
import re
import string
import random
import argparse
from collections import namedtuple
from ipaddress import ip_address
import sys

IPAddr = namedtuple("IPAddr", "ip port")

# Actions
NONE = 0
SEND = 1
RECV = 2

# Destinations
NODST  = 0
REMOTE = 1
SOURCE = 2 # source of last received message.
VIA    = 3 # The Via header


def parseargs():
    parser = argparse.ArgumentParser(description='SIP UA')
    parser.add_argument('-i',      help='Listning IP address',     type=unicode, required='True')
    parser.add_argument('-p',      help='Listning port',           required='True', type=int)
    parser.add_argument('--sport', help='source port for sending', type=int, default=0  )
    parser.add_argument('--sf',    help='scenario',                required='True')
    parser.add_argument('-d',      help='destination IP and port')     
    return parser.parse_args()

def parseIP(ipstr):
    ip, separator, port = ipstr.rpartition(':')
    assert separator # separator (`:`) must be present
    port = int(port) # convert to integer
    ip = ip_address(unicode(ip.strip("[]"))) # convert to `IPv4Address` or `IPv6Address` 
    return ((str(ip), port), ip.version, "UDP")

def getSock(addr, version , transport):
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

    print "Local socket on = {0}:{1}".format( addr[0], addr[1])
    return sock



def getCommand(line):
    if line[0].isalpha():
        l = re.split('[^\w$.]+', line)
        if l[0] == 'send':
            return (SEND, l[1], l[2])
        elif l[0] == 'recv':
            return (RECV, l[1], '')
        else:
            print "ignoring unknown command", l[0]

    return (NONE, NODST, '')
        

def loadScenario(scen_name):
    scenario = []
    data = []
    cmd = (NONE, NODST)

    try:
        f = file(scen_name, 'r')
        for line in f:
            if cmd[0] != NONE:
                if line[0].isalpha():
                    if len(data):
                        data.append('\r\n')
                        scenario.append({'name':cmd[1], 'action':cmd[0], 'dest':cmd[2], 
                            'data':'\r\n'.join(data)})
                        data = []
                    cmd = getCommand(line.strip())
                else:
                    data_line = line.strip()
                    if data_line:
                        data.append(data_line)
            else:
                cmd = getCommand(line)

        if cmd[0] != NONE: #and len(data):
            data.append('\r\n')
            scenario.append({
                'name':cmd[1], 
                'action':cmd[0], 
                'dest':cmd[2], 
                'data':'\r\n'.join(data)})

        if len(scenario) == 0:
            print "Bad scenario"
            sys.exit(0)

        return scenario

    except IOError as e:
        print "scenario is missing"
        sys.exit(0)

def msg_getValue(name, val, var):
    if name == 'via':
        l = re.split('\s|;', val)
        if var[0] == 'addr':
            addr = parseIP(l[1])
            return (addr[0])


class Handler:
    def __init__(self, scenario, srvr, clnt, contxt):
        self.scenario = scenario
        self.srvr = srvr
        self.clnt = clnt
        self.contxt = contxt
        self.messages = {}
        self.tagval = str(random.randint(1111,9999))

    def getValue(self, var):
        var_seq = string.split(var, '.')
        if var_seq[0] == 'local':
            if var_seq[1] == 'ip':
                return str(self.srvr.getsockname()[0])
            elif var_seq[1] == 'port':
                return str(self.srvr.getsockname()[1])
        elif var_seq[0] == 'server':
            if len(var_seq) == 1:
                return self.contxt['remote'][0]
            if var_seq[1] == 'ip':
                return self.contxt['remote'][0][0]
            elif var_seq[1] == 'port':
                return str(self.contxt['remote'][0][1])
        elif var_seq[0] == 'tag':
            return self.tagval
        elif self.messages.has_key(var_seq[0]):
            if len(var_seq) == 2:
                return self.messages[var_seq[0]][var_seq[1]]
            else:
                return msg_getValue(var_seq[1], 
                        self.messages[var_seq[0]][var_seq[1]], var_seq[2:])
        else:
            print "unknown variable", var
            return ''
            



    def populate(self, msg, dst):
        msg_lst = re.split('\[|\]', msg)
        for i, item in enumerate(msg_lst):
            if item[0] == '$':
                msg_lst[i] = self.getValue(item[1:])
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
        if dest[0] == '$':
            addr = self.getValue(dest[1:])
        else:
            addr = parseIP(dest)[0]
        req = self.populate(data, addr)
        print "sending to", addr
        print req

        self.clnt.sendto(req, addr);
        return req



    def recv(self, match):
        data, addr = self.srvr.recvfrom(1024)
        print "received from", addr, "\n", data
        print
        return data, addr;


    def execute(self):
        for a in self.scenario:
            if a['action'] == SEND:
                print "executing send:"
                msg = self.send(a['data'], a['dest'])
                self.save_msg(a['name'], msg)
            elif a['action'] == RECV:
                print "executing recv:"
                dt = ''
                if a.has_key('data'):
                    dt = a['data']
                msg, addr = self.recv(dt)
                self.save_msg(a['name'], msg, src=addr)
            else:
                print "unknow action", a['action']


def main(args):
    context = {'sport':args.sport}
    addr = ip_address(args.i)
    ServerAddr = ((str(addr), int(args.p)), addr.version, "UDP")
    if args.d:
        context['remote'] = parseIP(args.d)

    sock_srvr = getSock(ServerAddr[0], ServerAddr[1], ServerAddr[2])
    sock_clnt = getSock((ServerAddr[0][0], int(args.sport)),ServerAddr[1], ServerAddr[2])

    scenario = loadScenario(args.sf)
    loop = False
    if scenario[0]['action'] == RECV:
        loop = True
    
    hdlr = Handler(scenario, sock_srvr, sock_clnt, context)
    while True:
        hdlr.execute()
        if not loop:
            break


if __name__ == "__main__":
    main(parseargs())

