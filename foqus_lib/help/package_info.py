#
# This file is just to keep the third party library
# information together so a can update it easily.
#
import sys
import os
# FOQUS won't run without numpy or scipy, so I'll go ahead and try
# to import them, so I can extract information about them
import numpy
import scipy
# Depending on the platform and versions these modules my or may not
# be present.  I'll try to import them and get information if they are
# not available just assume I'm not using them
try:
    import PySide
    from PySide import QtCore
except:
    PySide = None
try:
    import matplotlib
except:
    matplotlib = None
try:
    import pyparsing
except:
    pyparsing = None
try:
    import win32api
except:
    win32api = None
try:
    import dateutil
except:
    dateutil = None
try:
    import ntlm
except:
    ntlm = None
try:
    import requests
except:
    requests = None
try:
    import py4j
except:
    py4j = None
try:
    import networkx
except:
    networkx = None
try:
    import Crypto
except:
    Crypto = None
try:
    import nlopt
except:
    nlopt = None
try:
    import adodbapi
except:
    adodbapi = None


def getThirdPartyInfo():
    third_party_modules = dict()
    myloc = os.path.dirname(os.path.abspath(__file__))
    lic = None
    with open(os.path.join(myloc,"LICENSE/Python_license.txt"), "r") as f: lic = f.read()
    third_party_modules["Python"] = {
        'version' : sys.version.split(' ')[0],
        'copyright' : "Copyright (c) 2001-2013 Python Software Foundation; All Rights Reserved",
        'url' : 'http://www.python.org',
        'url_source' : 'http://www.python.org/download/',
        'license' : lic,
        'summary' : "FOQUS is written in Python, so the Python interpretor is required to run it."}
    lic = None
    with open(os.path.join(myloc,"LICENSE/cma.txt"), "r") as f: lic = f.read()
    third_party_modules["cma"] = {
        'version' : "1.1.02",
        'copyright' : "Copyright (c) 2014 Inria",
        'author' : 'Nikolaus Hansen, 2008-2014',
        'url' : 'https://www.lri.fr/~hansen/cmaesintro.html',
        'url_source' : 'https://www.lri.fr/~hansen/cmaes_inmatlab.html#python',
        'license' : lic,
        'summary' : "Algorithm for the CMA-ES optimization plug-in"}
    lic = None
    with open(os.path.join(myloc,"LICENSE/Numpy_license.txt"), "r") as f: lic = f.read()
    third_party_modules["numpy"] = {
        'version' :	numpy.__version__,
        'copyright' : 'Copyright (c) 2005-2013, NumPy Developers; All Rights Reserved' ,
        'url' : 'http://www.numpy.org/',
        'url_source' : 'http://sourceforge.net/projects/numpy/files/NumPy/',
        'license' : lic,
        'summary' : "Numpy is a Python module used to perform fast calculations on arrays.  Numpy is used throughout FOQUS for numerical data."}
    lic = None
    with open(os.path.join(myloc,"LICENSE/Scipy_license.txt"), "r") as f: lic = f.read()
    third_party_modules["scipy"] = {
        'version' : scipy.__version__,
        'copyright' : 'Copyright (c) 2003-2013, SciPy Developers; All Rights Reserved' ,
        'url' : 'http://www.scipy.org/',
        'url_source' : 'http://sourceforge.net/projects/scipy/files/scipy/',
        'license' : lic,
        'summary' : "Scipy is a module for python that provides common numerical methods.  Scipy is used by the UQ portion of FOQUS, and some optimization plug-ins"}
    if PySide is not None:
        lic = None
        with open(os.path.join(myloc,"LICENSE/PySide_license.txt"), "r") as f: lic = f.read()
        third_party_modules["PySide"] = {
            'version' : PySide.__version__,
            'copyright' : 'Copyright (C) 2013 Digia Plc and/or its subsidiary(-ies); All Rights Reserved.' ,
            'url' : 'http://qt-project.org/wiki/PySide',
            'url_source' : 'http://qt-project.org/wiki/Get-PySide',
            'license' : lic,
            'summary' : "PySide is a Python API for Qt.  The PySide/Qt library is used for the FOQUS graphical interface."
        }
        lic = None
        with open(os.path.join(myloc,"LICENSE/Qt_license.txt"), "r") as f: lic = f.read()
        third_party_modules["Qt"] = {
            'version' : QtCore.qVersion(),
            'copyright' : 'Copyright (C) 2013 Digia Plc and/or its subsidiary(-ies); All Rights Reserved' ,
            'url' : 'http://qt-project.org/',
            'url_source' : 'http://qt-project.org/downloads',
            'license' : lic,
            'summary' : "Qt is the graphical toolkit used to create the FOQUS graphical interface."}
    if matplotlib is not None:
        lic = None
        with open(os.path.join(myloc,"LICENSE/Matplotlib_license.txt"), "r") as f:
            lic = f.read()
        third_party_modules["matplotlib"] = {
            'version' : matplotlib.__version__,
            'copyright' : 'Copyright (c) 2013, Matplotlib Development Team; All Rights Reserved',
            'url' : 'htp://matplotlib.org',
            'url_source' : 'http://matplotlib.org/downloads.html',
            'license' : lic,
            'summary' : "Matplotlib is a plotting library for Python, and used to create graphical representations of data in FOQUS."}
    if pyparsing is not None:
        lic = None
        with open(os.path.join(myloc,"LICENSE/pyparsing_license.txt"), "r") as f: lic = f.read()
        third_party_modules["pyparsing"] = {
            'version' : pyparsing.__version__,
            'copyright' : 'Copyright (c) 2003-2013, Paul T. McGuire; All Rights Reserved',
            'url' : 'http://pyparsing.wikispaces.com/',
            'url_source' : 'http://sourceforge.net/projects/pyparsing/files/',
            'license' : lic,
            'summary' : "Pyparsing is required by Matplotlib.  It is also being considered for future use in parsing mathematical expressions in FOQUS."}
    if win32api is not None:
        lic = None
        with open(os.path.join(myloc,"LICENSE/pywin32_license.txt"), "r") as f: lic = f.read()
        third_party_modules["pywin32"] = {
            'version' : "build 218",
            'copyright' : 'Copyright (c) 1994-2008, Mark Hammond; All rights reserved' ,
            'url' : 'http://sourceforge.net/projects/pywin32/',
            'url_source' : 'http://sourceforge.net/projects/pywin32/files/pywin32/',
            'license' : lic,
            'summary' : "Pywin32 provides an interface for Windows specific features to Python.  It is used to provide short file names without spaces to PSUADE for the UQ portion of FOQUS."}
    if dateutil is not None:
        lic = None
        with open(os.path.join(myloc,"LICENSE/python-dateutils_license.txt"), "r") as f: lic = f.read()
        third_party_modules["python-dateutils"] = {
            'version' : dateutil.__version__,
            'copyright' : 'Copyright (c) 2003-2011, Gustavo Niemeyer; All right reserved' ,
            'url' : 'http://labix.org/python-dateutil',
            'url_source' : 'http://labix.org/python-dateutil',
            'license' : lic,
            'summary' : "Dateutils is used by Matplotlib and the Turbine Client libraries."}
    if ntlm is not None:
        lic = None
        with open(os.path.join(myloc,'LICENSE/python-ntlm_license.txt'), "r") as f: lic = f.read()
        third_party_modules["python-ntlm"] = {
            'version' : "1.0.1",
            'copyright' : 'Copyright (c) 2001 Dmitry A. Rozmanov; All rights reserved' ,
            'url' : 'https://code.google.com/p/python-ntlm/',
            'url_source' : 'https://code.google.com/p/python-ntlm/source/checkout',
            'license' : lic,
            'summary' : "Python-ntlm is used for authentication features in the Turbine Client library"}
    if py4j is not None:
        lic = None
        with open(os.path.join(myloc,'LICENSE/py4j_license.txt'), "r") as f:
            lic = f.read()
        third_party_modules["Py4J"] = {
            'version' : "0.8.1",
            'copyright' : 'Copyright (C) 2009, Barthelemy Dagenais' ,
            'url' : 'http://py4j.sourceforge.net/index.html',
            'url_source' : 'https://github.com/bartdag/py4j',
            'license' : lic,
            'summary' : "Py4J is used to run data managment framework java code"}
    if networkx is not None:
        lic = None
        with open(os.path.join(myloc,'LICENSE/networkx_license.txt'), "r") as f: lic = f.read()
        third_party_modules["networkx"] = {
            'version' : networkx.__version__,
            'copyright' : 'Copyright (C) 2004-2012, NetworkX Developers' ,
            'url' : 'https://networkx.github.io/',
            'url_source' : 'https://networkx.github.io/download.html',
            'license' : lic,
            'summary' : "networkx is used to display file relationships in the data managment framework"}
    if nlopt is not None:
        lic = None
        with open(os.path.join(myloc,'LICENSE/nlopt_license.txt'), "r") as f:
            lic = f.read()
        third_party_modules["nlopt"] = {
            'version' : ".".join(map(str, [nlopt.version_major(),  nlopt.version_minor(), nlopt.version_bugfix()])),
            'copyright' : 'Copyright (C) 2007-2010 Massachusetts Institute of Technology' ,
            'url' : 'http://ab-initio.mit.edu/wiki/index.php/NLopt',
            'url_source' : 'http://ab-initio.mit.edu/wiki/index.php/NLopt',
            'license' : lic,
            'summary' : "Several DFO solvers from the nlopt library are available in FOQUS."}
    if Crypto is not None:
        lic = None
        with open(os.path.join(myloc,'LICENSE/pycrypto_license.txt'), "r") as f:
            lic = f.read()
        third_party_modules["pycrypto"] = {
            'version' : ".".join(map(str, Crypto.version_info)),
            'copyright' : 'Public Domain/Copyright (C) 2001-2003 Python Software Foundation',
            'url' : 'https://www.dlitz.net/software/pycrypto/',
            'url_source' : 'https://www.dlitz.net/software/pycrypto/',
            'license' : lic,
            'summary' : "Used for data managment framework."}
    if adodbapi is not None:
        lic = None
        with open(os.path.join(myloc,'LICENSE/adodbapi_license.txt'), "r") as f:
            lic = f.read()
        third_party_modules["adodbapi"] = {
            'version' : adodbapi.version.replace("adodbapi v", ""),
            'copyright' : "Copyright (C) 2002 Henrik Ekelund, versions 2.1 and later by Vernon Cole",
            'url' : 'http://adodbapi.sourceforge.net/',
            'url_source' : 'http://sourceforge.net/projects/adodbapi/',
            'license' : lic,
            'summary' : "Used to interact directly with TurbineLite database."}

    # --------------------------------------------------------------------------
    # Begin non Python dependencies (Java)
    # --------------------------------------------------------------------------

    # D3
    lic = None
    with open(os.path.join(myloc, "LICENSE/d3_license.txt"), "r") as f:
        lic = f.read()
    third_party_modules["D3"] = {
        'version': "3.5.6",
        'copyright': "Copyright (C) 2015 Mike Bostock.",
        'url': "http://d3js.org/",
        'license': lic,
        'url_source':  "https://github.com/mbostock/d3",
        'summary': ("Used for displaying graph dependencies "
                    "in data management framework.")}

    # SLF4J
    lic = None
    with open(os.path.join(myloc, "LICENSE/slf4j_license.txt"), "r") as f:
        lic = f.read()
    third_party_modules["SLF4J"] = {
        'version':  "1.7.10",
        'copyright': "Copyright (C) 2004-2013 QOS.ch",
        'url': "http://www.slf4j.org/",
        'license': lic,
        'url_source': "https://github.com/qos-ch/slf4j",
        'summary': "Used by DMF Java component for logging"
        }

    # JSON.org
    lic = None
    with open(os.path.join(myloc, "LICENSE/json_org_license.txt"), "r") as f:
        lic = f.read()
    third_party_modules["JSON.org"] = {
        'version':  "20150729",
        'copyright': "Copyright (C) 2002 JSON.org",
        'url': "http://www.json.org/java/index.html",
        'license': lic,
        'url_source': "https://github.com/douglascrockford/JSON-java",
        'summary': "Used by DMF Java component to handle JSON"
        }
    # --------------------------------------------------------------------------
    # End of Non Python dependencies (Java)
    # --------------------------------------------------------------------------
    return third_party_modules

if __name__ == "__main__":
    info = getThirdPartyInfo()
    print info["nlopt"]["version"]
    print info["pycrypto"]["version"]
