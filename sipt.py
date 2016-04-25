import re
import argparse
import sys
from handler import *



def parseargs():
    parser = argparse.ArgumentParser(description='SIP UA')
    parser.add_argument('-i',      help='Listning IP address',     type=unicode, required='True')
    parser.add_argument('-p',      help='Listning port',           required='True', type=int)
    parser.add_argument('--sport', help='source port for sending', type=int, default=0  )
    parser.add_argument('--sf',    help='scenario',                required='True')
    parser.add_argument('-d',      help='destination IP and port')     
    return parser.parse_args()




# Formate is: (0)command (1)name (2)destination
def readCommand(line):
    if line[0].isalpha():
        l = re.split('[^\w$.]+', line)
        if l[0] == 'send':
            return (Handler.SEND, l[1], l[2])
        elif l[0] == 'recv':
            return (Handler.RECV, l[1], '')
        else:
            print "ignoring unknown command", l[0]

    return (Handler.NONE, Handler.NODST, '')
        

def loadScenario(scen_name):
    scenario = []
    data = []
    cmd = (Handler.NONE, Handler.NODST)

    try:
        f = file(scen_name, 'r')
        for line in f:
            if cmd[0] != Handler.NONE:
                if line[0].isalpha():
                    if len(data):
                        data.append('\r\n')
                        scenario.append({'name':cmd[1], 'action':cmd[0], 'dest':cmd[2], 
                            'data':'\r\n'.join(data)})
                        data = []
                    cmd = readCommand(line.strip())
                else:
                    data_line = line.strip()
                    if data_line:
                        data.append(data_line)
            else:
                cmd = readCommand(line)

        if cmd[0] != Handler.NONE: #and len(data):
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




def main(args):
    addr = ip_address(args.i)

    ServerAddr = IPAddr(addr=(str(addr), int(args.p)),     version=addr.version)
    ClientAddr = IPAddr(addr=(str(addr), int(args.sport)), version=addr.version)
    scenario = loadScenario(args.sf)

    context = {}
    if args.d:
        context['remote'] = parseIP(args.d)

    
    loop = False
    if scenario[0]['action'] == Handler.RECV:
        loop = True
    
    hdlr = Handler(scenario, ServerAddr, ClientAddr, context)
    while True:
        hdlr.execute()
        if not loop:
            break


if __name__ == "__main__":
    main(parseargs())

