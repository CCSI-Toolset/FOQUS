# This file is used to fix a part of matplotlib so that it
# gets picked up by py2exe.  This is only used when building
# an exe on windows
import os
import mpl_toolkits
pth = mpl_toolkits.__path__[0]
f = open(os.path.join(pth, '__init__.py'), 'w')
f.close()
