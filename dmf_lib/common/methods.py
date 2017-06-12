import os
import sys
import hashlib
import platform

from StringIO import StringIO
from ConfigParser import RawConfigParser
from math import log

from dmf_lib.common.common import IP_ADDRESS
from dmf_lib.common.common import PORT
from dmf_lib.common.common import PROTOCOL
from dmf_lib.common.common import PROP_HEADER
from dmf_lib.common.common import PRINT_COLON
from dmf_lib.common.common import REPO_NAME
from dmf_lib.common.common import REPO_PROPERTIES_UNIX_PATH
from dmf_lib.common.common import REPO_PROPERTIES_WIN_PATH
from dmf_lib.common.common import SEMI_COLON
from dmf_lib.common.common import TMP_KEYS_EXT
from dmf_lib.common.common import UNIX_PATH_SEPARATOR
from dmf_lib.common.common import VALID_PROP_KEYS
from dmf_lib.common.common import WINDOWS
from dmf_lib.common.common import WIN_PATH_SEPARATOR


class Common():
    '''Provides some common functions shared between a number of files.'''

    def validateAndGetKeyProps(self, prop, verbose=True):
        ''' Validate stored keys '''
        if verbose:
            sys.stdout.write("\t"+prop + "... ")

        config = StringIO()
        config.write('[' + PROP_HEADER + ']\n')
        config.write(open(prop).read())
        config.seek(0, os.SEEK_SET)
        rcp = RawConfigParser()
        rcp.optionxform = str
        rcp.readfp(config)

        is_valid = True
        valid_prop = VALID_PROP_KEYS[:]
        for k, v in rcp.items(PROP_HEADER):
            if k not in VALID_PROP_KEYS:
                if verbose:
                    if is_valid:
                        sys.stdout.write("ERROR")
                    sys.stdout.write("\n\t\tInvalid key: %s" % k)
                is_valid = False
            else:
                valid_prop.remove(k)

        if len(valid_prop) > 0:
            if verbose:
                if is_valid:
                    sys.stdout.write("INCOMPLETE")
                sys.stdout.write("\n\t\tMissing key(s): %s" % str(valid_prop))
            is_valid = False

        try:
            IP = rcp.get(PROP_HEADER, IP_ADDRESS)
            if IP.lower() == "localhost":
                if verbose:
                    if is_valid:
                        sys.stdout.write("INVALID IP ADDRESS")
                    sys.stdout.write("\n\t\tInvalid IP: %s" % IP)
                is_valid = False
        except:
            pass

        if is_valid:
            if verbose:
                print "OK"
            repo_name = rcp.get(PROP_HEADER, REPO_NAME)
            url = rcp.get(PROP_HEADER, PROTOCOL) \
                + rcp.get(PROP_HEADER, IP_ADDRESS) + ":"\
                + rcp.get(PROP_HEADER, PORT)
            return_vals = [repo_name, url]
            return True, return_vals
        else:
            if verbose:
                print
            return False, None

    def convertBytesToReadable(self, bytes, si):
        ''' Convert bytes to readable format '''
        base = 1000 if si else 1024
        if bytes < base:
            return str(bytes) + " bytes"

        exp = int(log(bytes) / log(base))
        unit = "kMGTPE"[exp - 1] + "B" if si else "KMGTPE"[exp - 1] + "iB"
        return str(bytes / pow(base, exp)) + " " + unit

    def deleteCachedCredentials(self):
        ''' Delete cached credentials '''
        try:
            # We are on Windows
            if platform.system().startswith(WINDOWS):
                PROP_LOC = (
                    os.environ[REPO_PROPERTIES_WIN_PATH] +
                    WIN_PATH_SEPARATOR)
            else:
                PROP_LOC = (
                    os.environ[REPO_PROPERTIES_UNIX_PATH] +
                    UNIX_PATH_SEPARATOR)
            keys = [f for f in os.listdir(PROP_LOC)
                    if os.path.isfile(os.path.join(PROP_LOC, f))
                    and f.endswith(TMP_KEYS_EXT)]
            if len(keys) > 0:
                os.remove(PROP_LOC+keys[0])
        except OSError, e:
            print self.__class__.__name__, PRINT_COLON, e

    def splitDMFID(self, dmf_id):
        ''' Splits a DMF ID and returns an object ID and version number '''
        dmf_id_parts = dmf_id.split(SEMI_COLON)
        try:
            id = dmf_id_parts[0]
            ver = dmf_id_parts[1]
            return id, ver
        except:
            err = "ID: " + dmf_id + " has incorrect format!"
            print self.__class__.__name__, PRINT_COLON, err
            return None, None

    def concatVersion(self, major_version, minor_version):
        return str(major_version) + '.' + str(minor_version)

    def splitVersion(self, version):
        try:
            version = version.split('.')
            major_version = int(version[0])
            minor_version = int(version[1])
            return (major_version, minor_version)
        except:
            return (None, ) * 2

    def isVersion1OlderThanVersion2(self, ver1, ver2):
        ver1_parts = ver1.split('.')
        ver1_major = ver1_parts[0]
        ver1_minor = ver1_parts[1]

        ver2_parts = ver2.split('.')
        ver2_major = ver2_parts[0]
        ver2_minor = ver2_parts[1]

        if int(ver1_major) < int(ver2_major):
            return True
        elif int(ver1_minor) < int(ver2_minor):
            return True
        else:
            return False

    def convertJavaBool2PyBool(self, b):
        ''' Converts Java string boolean to a Python boolean '''
        if b is None:
            return b
        else:
            if b == "true":
                return True
            elif b == "false":
                return False
            else:
                return None

    def getChecksum(self, b):
        ''' Returns checksum for a bytearray'''
        return hashlib.sha1(b).hexdigest()

    def getNewJavaHomeForWindowsEnv(self, java_home):
        ''' Simple function that reformats JAVA_HOME for Windows'''
        # Strip quotes
        new_java_home = java_home.strip('"\'')
        # Windows special case. Length < 3 for java home
        # directly in top directory, e.g. C:\ #
        if len(java_home) > 3:
            # First case: JAVA_HOME not in quotes
            if java_home[-1] == '\\' \
                    and java_home[-2] != ':':
                new_java_home = java_home[:-1]
                print "Backslash detected in %JAVA_HOME%, removing backslash."
                print "%JAVA_HOME% is now", new_java_home
            # Second case: JAVA_HOME in quotes
            elif java_home[-1] == '"' \
                    and java_home[-2] == '\\' \
                    and java_home[-3] != ':':
                new_java_home = java_home[:-2] + '"'
                print "Backslash detected in %JAVA_HOME%, removing backslash."
                print "%JAVA_HOME% is now", new_java_home
        return new_java_home
