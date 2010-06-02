#! /usr/bin/env python


# Copyright LAAS/CNRS 2009-2010
# Authors Duong Dang

import getopt,sys, warnings, imp, os, imp

corba_path = os.path.dirname(os.path.abspath(__file__)) + '/corba'
sys.path = [corba_path] + sys.path
# Import the CORBA module
from omniORB import CORBA

# Import the stubs for the CosNaming and hppCorbaServer modules

import hppCorbaServer
import CosNaming

# Initialise the ORB
orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)

# Obtain a reference to the root naming context
obj         = orb.resolve_initial_references("NameService")
rootContext = obj._narrow(CosNaming.NamingContext)

if rootContext is None:
    print "Failed to narrow the root naming context"
    sys.exit(1)

# Resolve the name "test.my_context/ExampleEcho.Object"
name = [CosNaming.NameComponent("sot", "context"),
        CosNaming.NameComponent("coshell", "servant")]

try:
    obj = rootContext.resolve(name)

except CosNaming.NamingContext.NotFound, ex:
    print "Name not found"
    sys.exit(1)

# Narrow the object to an hppCorbaServer::SOT_Server_Command
req_obj = obj._narrow(hppCorbaServer.SOT_Server_Command)

if req_obj is None:
    print "Object reference is not an Example::Echo"
    sys.exit(1)

# Invoke the echoString operation

def runAndReadWrap(cmd_str):
    """
    """
#    print "calling %s"%cmd_str
    return req_obj.runAndRead(cmd_str)

def main():
    """
    """
    print runAndReadWrap(' '.join(sys.argv[1:]))

if __name__ == '__main__':
    main()
