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
    parser.add_argument('--hp',    help='hide port if it is 5060', action='store_true')
    parser.add_argument('--step',  help='step through scenario',   action='store_true')
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

    ver = 6 if re.search('^[a-f0-9:]+$', args.i) else 4
    ServerAddr = IPAddr(args.i, args.p, ver)
    ClientAddr = IPAddr(args.i, args.sport, ver)
    scenario = loadScenario(args.sf)

    if args.d:
        g_context['remote'] = IPAddr.from_string(args.d)
    g_context['hidePort'] = args.hp
    g_context['step'] = args.step

    
    loop = False
    if scenario[0]['action'] == Handler.RECV:
        loop = True
    
    hdlr = Handler(scenario, ServerAddr, ClientAddr)
    while True:
        hdlr.execute()
        if not loop:
            resp = raw_input('Continue y/n:')
            if resp == 'n':
                break


if __name__ == "__main__":
    main(parseargs())

