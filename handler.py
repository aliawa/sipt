from collections import namedtuple
#from ipaddress import ip_address
import socket
import string
import random
import re

# vars 
# local.ip   local.port   local.addr
# remote.ip  remote.port  remote.addr
# <msg>.<header>

g_context = {}


class IPAddr:
    def __init__(self, ip, port, ver):
        self.ip = ip
        self.port = port
        self.version = ver

    @classmethod
    def from_string(cls, ipstr):
        ipv4 = re.compile('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?:\s*:\s*(\d{1,5}))?')
        ipv6 = re.compile('\[?([:0-9a-f]+)\]?(?:\s*:\s*([0-9]{1,5}))?')
        ip = ''
        port = 0
        ver = 0
        m = ipv4.match(ipstr)
        if m:
            ip = m.group(1)
            port = int(m.group(2)) if m.group(2) else 0
            ver = 4
        else:
            m = ipv6.match(ipstr)
            if m:
                ip = m.group(1)
                port = int(m.group(2)) if m.group(2) else 0
                ver = 6
        return cls(ip, port, ver)

    def get_ip(self):
        return self.ip
    def get_version(self):
        return self.version
    def get_port(self):
        return self.port
    def get_addr(self):
        return (self.ip, self.port)
    def __repr__(self):
        if g_context['hidePort'] == False or self.port != 5060:
            if self.version == 6:
                return "[{0}]:{1}".format(self.ip, str(self.port))
            else:
                return "{0}:{1}".format(self.ip, str(self.port))
        return self.ip
        



class Handler:
    # Actions
    NONE = 0
    SEND = 1
    RECV = 2

    # Destinations
    NODST  = 0

    def __init__(self, scenario, srvr_addr, clnt_addr):
        self.scenario = scenario
        self.srvr_addr = srvr_addr
        self.clnt_addr = clnt_addr
        
        self.messages = {}
        self.srvr_sock = self.getSock(srvr_addr.get_addr(), 
                srvr_addr.get_version(), "UDP")
        self.clnt_sock = self.getSock(clnt_addr.get_addr(), 
                clnt_addr.get_version(), "UDP")
        self.tagval = str(random.randint(1111,9999))
        self.media_ports = [random.randint(11111,11999)]

        print "Listning on : ", srvr_addr
        print "Sending from: ", clnt_addr
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


    def msg_getValue(self, name, val, var):
        if name == 'via':
            l = re.split('\s|;', val)
            if var[0] == 'addr':
                return IPAddr.from_string(l[1])



    def getValue(self, var, env={}):
        var_seq = string.split(var, '.')
        if var_seq[0] == 'local':
            if var_seq[1] == 'ip':
                return self.srvr_addr.get_ip()
            elif var_seq[1] == 'port':
                return self.srvr_addr.get_port()
            elif var_seq[1] == 'addr':
                return self.srvr_addr
            elif var_seq[1] == 'ver':
                return self.srvr_addr.get_version()
            elif var_seq[1] == 'audioport':
                return self.media_ports[0]

        elif var_seq[0] == 'server':
            if var_seq[1] == 'ip':
                return g_context['remote'].get_ip()
            elif var_seq[1] == 'port':
                return g_context['remote'].get_port()
            elif var_seq[1] == 'addr':
                return g_context['remote']

        elif var_seq[0] == 'tag':
            return self.tagval

        elif var_seq[0] == 'len':
            return env['len']
            
        elif self.messages.has_key(var_seq[0]):
            if len(var_seq) == 2:
                # The entire header
                return self.messages[var_seq[0]][var_seq[1]]
            else:
                return self.msg_getValue(var_seq[1], 
                        self.messages[var_seq[0]][var_seq[1]], var_seq[2:])
        else:
            print "unknown variable", var
            return ''




    def populate(self, msg, env):
        msg_lst = re.split('\[|\]', msg)
        for i, item in enumerate(msg_lst):
            if item and item[0] == '$':
                msg_lst[i] = str(self.getValue(item[1:], env))
        return ''.join(msg_lst)



    def save_msg(self, name, msg, src=''):
        print "saving:", name
        msg_parts = msg.split('\r\n\r\n')
        msg = msg_parts[0]
        body = ''
        msg_dct = {}
        if len(msg_parts) > 1:
            body = msg_parts[1].strip()
            msg_dct['body'] = body

        msg_lst = msg.split('\r\n')
        msg_dct['first'] = msg_lst[0]
        for item in msg_lst[1:]:
            l = item.split(':',1)
            key = string.lower(l[0].strip())
            if key:
                msg_dct[key] = l[1].strip()
        if src:
            msg_dct['src'] = src

        self.messages[name] = msg_dct



    def send(self, data, body, dest):
        if dest == '': # dest not given -> use remote
            addr = self.getValue('server.addr')
        elif dest[0] == '$':
            addr = self.getValue(dest[1:])
        else:
            addr = IPAddr.from_string(dest)

        msg_dst = addr.get_addr()
        if msg_dst[1] == 0:
            msg_dst = (msg_dst[0], 5060)

        print "\nsending to", msg_dst
        env = {}
        bdy = ''
        if len(body):
            bdy = self.populate(body, env)
            env['len'] = len(bdy)

        req = self.populate(data, env)
        if len(bdy):
            req = "{}\r\n\r\n{}".format(req, bdy)

        print ("--->>>\n{}\n--->>>".format(req))

        self.clnt_sock.sendto(req, msg_dst);
        return req



    def recv(self, match):
        data, addr = self.srvr_sock.recvfrom(1024)
        print ("\nreceived from:{}\n<<<---\n{}\n<<<---".format(addr, data.strip()))
        return data, addr;



    def execute(self):
        for a in self.scenario:
            if a['action'] == 'send':
                print "executing send:"

                if g_context['step']:
                    b = raw_input('b = break; any = continue')
                    if b == 'b':
                        break

                msg = self.send(a['msg'], a['body'], a['dest'])
                self.save_msg(a['name'], msg)
            elif a['action'] == 'recv':
                print "executing recv:"
                dt = ''
                if a.has_key('msg'):
                    dt = a['msg']
                msg, addr = self.recv(dt)
                self.save_msg(a['name'], msg, src=addr)
            else:
                print "unknow action", a['action']


if __name__ == "__main__":
    A =  [ 'fd99:2217:498e::15',
            '[fd99:2217:498e::15]:5060',
            '[fd99:2217:498e::15]',
            '10.3.36.15',
            '10.3.36.15:5060' ]
    B = [False,True]

    for i in range(0,2):
        g_context['hidePort'] = B[i]
        for adr in A:
            ipadr = IPAddr.from_string(adr)
            print "ip={0}\tport={1}\tversion={2}".format(ipadr.get_ip(), ipadr.get_port(), 
                    ipadr.get_version())



