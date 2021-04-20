"""SinterFileVectorize.py
* Contains a function to modify and extend an existing json file, \
    to include vector variables.

See LICENSE.md for license and copyright details.
"""
import sys
import json
import copy
from collections import OrderedDict
import os
import ast
import win32com
from win32com import client as win32

# Take vector names and size from user interface before calling the sintervectorize function

def sintervectorize(json_file,input_vectors,output_vectors,vectorized_json_file):
    # Decode the current json file
    f=open(json_file)
    sc = json.load(f)
    f.close()
    
    # Access the Aspen file used in the json file
    aspen=win32.Dispatch('Apwn.Document')
    aspen.InitFromArchive2(os.path.abspath(sc["model"]["file"]))
    
    # # Depending on the vector names and size, modify the json contents, and encode the file again
    input_vectors = ast.literal_eval(input_vectors)
    if input_vectors is not None:
        for v in input_vectors:
            i=0
            for ipname,details in sc['inputs'].copy().items():
                if v[0] in details['path'][0]:
                    ipname2 = v[0] + '_{0}'.format(i)
                    sc['inputs'][ipname2] = sc['inputs'].pop(ipname)
                    sc['inputs'][ipname2]['vector'] = v[0]
                    sc['inputs'][ipname2]['index'] = i
                    i+=1
            while i<v[1]-1:
                ipname_new = v[0] + '_{0}'.format(i)
                ipname_prev = v[0] + '_{0}'.format(i-1)
                sc['inputs'][ipname_new] = sc['inputs'][ipname_prev]
                vector_element = '\\{0}\\'.format(i-1)
                sc['inputs'][ipname_new]['path'][0] = sc['inputs'][ipname_prev]['path'][0].replace(vector_element,'\\{0}\\'.format(i))
                sc['inputs'][ipname_new]['default'] = aspen.Tree.FindNode(sc['inputs'][ipname_new]['path'][0]).Value
                sc['inputs'][ipname_new]['vector'] = v[0]
                sc['inputs'][ipname_new]['index'] = i
                i+=1
        aspen.Close()
    
    output_vectors = ast.literal_eval(output_vectors)
    if output_vectors is not None:
        for v in output_vectors:
            i=0
            for opname,details in sc['outputs'].copy().items():
                if v[0] in details['path'][0]:
                    opname2 = v[0] + '_{0}'.format(i)
                    sc['outputs'][opname2] = sc['outputs'].pop(opname)
                    sc['outputs'][opname2]['vector'] = v[0]
                    sc['outputs'][opname2]['index'] = i
                    i+=1
            while i<=v[1]-1:
                opname_new = v[0] + '_{0}'.format(i)
                opname_prev = v[0] + '_{0}'.format(i-1)
                sc['outputs'][opname_new] = dict()
                sc['outputs'][opname_new] = sc['outputs'][opname_prev].copy()
                vector_element = "\\{0}\\".format(i)
                prev_path = copy.copy(sc['outputs'][opname_prev]['path'][0])
                sc['outputs'][opname_new]['path'] = [prev_path.replace(str(vector_element),"\\{0}\\".format(i+1))]
                sc['outputs'][opname_new]['default'] = aspen.Tree.FindNode(sc['outputs'][opname_new]['path'][0]).Value
                sc['outputs'][opname_new]['vector'] = v[0]
                sc['outputs'][opname_new]['index'] = i
                i+=1
        aspen.Close()
    
    sc["title"] = vectorized_json_file.split('.')[0]
    f1 = open(vectorized_json_file, "w")
    json.dump(sc, f1, indent=2)
    f1.write("\n")
    f1.write("\n")
    f1.close()