# This is a function for adding all files in a
# directory and its subdirectories to a list.
# It is used by the FOQUS installer to make
# lists of data files to be installed when using
# py2exe.

import os	
import sys
    
def recursiveFiles(fdir, exclude = [], fileReletive = None, excludeDirs=[]):
    '''
        exclude a list of extensions of file type to exclude
        excludeDirs a list of sub dirs to exclude (top level)
    '''
    fileList = dict()
    fdir = os.path.abspath(fdir)
    listing = os.listdir(fdir)
    for item in listing:
        dir_item = os.path.join(fdir, item)
        if os.path.isfile(dir_item):
            inc = True
            for e in exclude:
                if item.endswith(e):
                    inc = False
                    break
            if inc:
                if not fileList.get(fdir, None):
                    fileList[fdir] = []
                fileList[fdir].append(os.path.join(fdir, item))
        elif os.path.isdir(dir_item):
            if item not in excludeDirs:
                fileList.update(recursiveFiles(dir_item, exclude))
    l = []
    for key, item in fileList.iteritems():
        if fileReletive:
            for i, f in enumerate(item):
                item[i] = os.path.relpath(f)[len(fileReletive)+1:]
        l.append((os.path.relpath(key), item))	
    return l
    
def recursiveFileList(fdir, exclude = [], fileReletive = None, excludeDirs=[]):
    l = recursiveFiles(fdir, exclude, fileReletive, excludeDirs)
    l2 = []
    for i, item in enumerate(l):
        l2 = l2 + item[1]
    return l2

if __name__ == "__main__":
    l = recursiveFileList(
        'dmf_lib/java', 
        ['.py', '.pyc'], 
        fileReletive = 'dmf_lib',
        excludeDirs = ['src'])
    #print l
        
