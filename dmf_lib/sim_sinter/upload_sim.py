import os
import sys
from PySide.QtGui import QApplication

dmf_home = os.sep.join(os.getcwd().split(os.sep)[:-2]) + '/'
sys.path.insert(1, dmf_home)

try:
    from dmf_lib.common.common import (
        DMF_LITE,
        DMF_HOME)
    from dmf_lib.dmf_browser import DMFBrowser
    useDMF = True
except:
    print ("Failed to import dmf_lib components")
    useDMF = False


def main():
    if not useDMF:
        return
    QApplication(sys.argv)
    os.environ[DMF_HOME] = dmf_home
    sim_bytestream = open("/Users/ycheah/Documents/ccsi/foqus/trunk/examples/iREVEAL/boiler_rom.bkp", "rb").read()
    sinter_config_bytestream = open("/Users/ycheah/Documents/ccsi/foqus/trunk/examples/iREVEAL/boiler.json", "rb").read()

    repo_name = DMF_LITE
    config = None  # DMF Lite does not require a config
    # sim_bytestream = None  # Insert simulation bytestream here

    sim_name = "Foo simulation"
    update_comment = ''  # Can change if wanted
    confidence = 'experimental'
    # sinter_config_bytestream = None  # Sinter config bytestream here
    sinter_config_name = str(sim_name) + "_sinter_config.json"
    resource_bytestream_list = []  # Put resource bystreams in a list here
    resource_name = []  # Put resource names in a list if needed
    print sys.argv[:]

    dmf_id_list = [sys.argv[-1]]
    does_exist_result = DMFBrowser.doFilesExist(
        None,
        config,
        repo_name,
        dmf_id_list)

    if does_exist_result:
        print does_exist_result
        sim_id = sys.argv[-1]
    else:
        sim_id = None

    sim_id, sinter_config_id, sinter_config_bytestream = \
        DMFBrowser.uploadSimulation(
            None,
            config,
            repo_name,
            sim_bytestream,
            sim_id,
            sim_name,
            update_comment,
            confidence,
            sinter_config_bytestream,
            sinter_config_name,
            resource_bytestream_list,
            resource_name)
    print "Stored with ID: ", sim_id

if __name__ == "__main__":
    # Takes in an optional argument of a DMF id. If no ID is given as a param,
    # will store as new simulation assuming simulation not already stored.
    main()
