#!/usr/bin/python
'''
    foqusALAMOClient.py
     
    * The purpose of this scrip is to be the simulator executable for
    * ALAMO.  It reads the input data from ALAMO sends it to FOQUS using
    * a network socket connection, waits for the results and writes them
    * in the format expected by ALAMO, then it closes the listener in 
    * FOQUS and exits.

    John Eslick, Carnegie Mellon University, 2014

    This Material was produced under the DOE Carbon Capture Simulation
    Initiative (CCSI), and copyright is held by the software owners:
    ORISE, LANS, LLNS, LBL, PNNL, CMU, WVU, et al. The software owners
    and/or the U.S. Government retain ownership of all rights in the 
    CCSI software and the copyright and patents subsisting therein. Any
    distribution or dissemination is governed under the terms and 
    conditions of the CCSI Test and Evaluation License, CCSI Master
    Non-Disclosure Agreement, and the CCSI Intellectual Property 
    Management Plan. No rights are granted except as expressly recited
    in one of the aforementioned agreements.
'''
import numpy as np
import time
import sys
from multiprocessing.connection import Client
import argparse

if __name__ == '__main__':
    # Set the socket address, maybe someday this will change or 
    # have some setting option, but for now is hard coded
    host = 'localhost'
    port = 56002
    # Read the samples from the input file made by ALAMO
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", 
        help = "Listener host")
    parser.add_argument("--port", 
        help = "Listener port")
    parser.add_argument("--run", action="store_true",
        help = "Specify a run type and start")
    parser.add_argument("-o", "--out", 
        help="Output file for run")
    parser.add_argument("--loadValues",
        help = "Load flowsheet variable values from json file")
    parser.add_argument("--quit", action="store_true",
        help = "Close down listener quit any running simulations")
    args = parser.parse_args()
    if args.host:
        host = args.host
    if args.port:
        port = args.port
    address = (host, port)
    conn = Client(address)
    if args.quit:
        conn.send(['quit'])
    else:
        if args.loadValues:
            conn.send(['loadValues', args.loadValues])
            print conn.recv()
        if args.run:
            conn.send(['run'])
            print conn.recv()
        if args.out:
            conn.send(['saveValues', args.out])
            print conn.recv()
        conn.send(['close'])
    conn.close()

