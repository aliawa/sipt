import re
import argparse
import sys
from handler import *
from enum import Enum



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




class STATE(Enum):
    cmd, msg, bdy, done = range(4)


# Formate is: (0)command (1)name (2)destination
def readCommand(line,cmd):
    if line[0].isalpha():
        l = re.split('[^\w$.]+', line)
        if l[0] in ['send','recv']:
            for x in l:
                cmd.append(x)
            return STATE.msg, True
        else:
            print "ignoring unknown command", l[0]

    return STATE.cmd, True



def readMsg(line, msg):
    if line[0].isalpha():
        return STATE.cmd, False
    else:
        data_line = line.strip()
        if data_line:
            msg.append(data_line)
        else:
            return STATE.bdy, True
        
    return STATE.msg, True
        

def readBody(line, bdy):
    if line[0].isalpha():
        return STATE.done, False
    else:
        data_line = line.strip()
        if data_line:
            bdy.append(data_line)
        else:
            return STATE.done, False 
        
    return STATE.bdy, True


def saveScenario(scenario, cmd, msg, bdy):
    scenario.append({'name':cmd[1], 'action':cmd[0], 'dest':cmd[2], 
        'msg':'\r\n'.join(msg),
        'body':'\r\n'.join(bdy)})
    return STATE.cmd, True


def loadScenario(scen_name):
    scenario = []
    msg = []
    bdy = []
    cmd = []
    state = STATE.cmd

    try:
        f = file(scen_name, 'r')
    except IOError as e:
        print "scenario is missing"
        sys.exit(0)

    for line in f:
        while True:
            if state == STATE.cmd:
                state, nxt = readCommand(line, cmd)
            elif state == STATE.msg:
                state, nxt = readMsg(line, msg)
            elif state == STATE.bdy:
                state, nxt = readBody(line, bdy)
            elif state == STATE.done:
                state, nxt = saveScenario(scenario, cmd, msg, bdy)
                msg = []
                bdy = []
                cmd = []
            if nxt:
                break;
    if state != STATE.cmd:
        saveScenario(scenario, cmd, msg, bdy)

    if len(scenario) == 0:
        print "Bad scenario"
        sys.exit(0)

    return scenario




def main(args):

    ver = 6 if re.search('^[a-f0-9:]+$', args.i) else 4
    ServerAddr = IPAddr(args.i, args.p, ver)
    ClientAddr = IPAddr(args.i, args.sport, ver)
    scenario = loadScenario(args.sf)


#     for action in scenario:
#         for key,val in action.items():
#             print key
#             print "-----"
#             print val
#         print

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

    
