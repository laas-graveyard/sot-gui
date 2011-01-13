#! /usr/bin/env python

# Copyright LAAS/CNRS 2009-2010
# Authors Duong Dang
from time import sleep
import sys, os
import robotviewer
import corba_util
import logging
sys.path.append(os.path.join( os.path.abspath(os.path.dirname(__file__)),
                              'idl'))
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

logger = logging.getLogger("rv-sot-bridge")
logger.addHandler(NullHandler())
logger.setLevel(logging.DEBUG)

def main():
    """
    """
    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    logger.addHandler(sh)

    sotobj = corba_util.GetObject("CorbaServer",'CorbaServer.SOT_Server_Command',[('sot','context'),('coshell','servant')])

    # guess robot type
    robot_type = sotobj.runAndRead('OpenHRP.help').split()[0][:-1]
    rvclient = robotviewer.client()

    def get_HRP_config():
        pos = sotobj.readVector("OpenHRP.state")
        wst = sotobj.readVector("dyn.ffposition")

        if len(wst) != 6:
            logger.warning("Wrong dimension of waist_pos, robot not updated")
            return None

        for i in range(len(wst)):
            pos[i] = wst[i]

        if robot_type == "RobotSimu":
            pos[2] += 0.105

        # dynsmall thingy
        if len(pos) == 36:
            pos_full = [0 for i in range(46)]
            for i in range(29):
                pos_full[i] = pos[i]
            for i in range(29,36):
                pos_full[i+5] = pos[i]
            return pos_full

        return pos

    while True:
        sleep(0.02)
        pos = get_HRP_config()
        if pos:
            rvclient.updateElementConfig('hrp',pos)
        else:
            logger.warning('Couldnt get robot config')

if __name__ == '__main__':
    main()
