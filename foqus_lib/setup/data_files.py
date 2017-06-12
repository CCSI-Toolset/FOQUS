# This is a function for adding all files in a
# directory and its subdirectories to a list.
# It is used by the FOQUS installer to make
# lists of data files to be installed when using
# py2exe.

import os	
    
def recursiveFiles(dir, exclude = []):
    fileList = dict()
    dir = os.path.abspath(dir)
    listing = os.listdir(dir)
    for item in listing:
        dir_item = os.path.join(dir, item)
        if os.path.isfile(dir_item):
            inc = True
            for e in exclude:
                if item.endswith(e):
                    inc = False
                    break
            if inc:
                if not fileList.get(dir, None):
                    fileList[dir] = []
                fileList[dir].append(os.path.join(dir, item))
        elif os.path.isdir( dir_item):
            fileList.update( recursiveFiles( dir_item, exclude ) )		
        l = []
        for key, item in fileList.iteritems():
            l.append( (os.path.relpath(key), item ) )	
    return l

if __name__ == "__main__":
    for item in recursiveFiles("framework", ['.py', '.pyc']):
        print item
