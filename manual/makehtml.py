import os
import shutil
import subprocess
import sys
import zipfile


#
# Get the figures directories.
#
dlist = os.listdir("./") # directory listing
figDirs = []
for item in dlist:
    item2 = os.path.join(item, 'figs')
    if item[0:6]=="Chapt_" and os.path.isdir(item2):
        figDirs.append(item2)
    if item[0:5]=="Figs_" and os.path.isdir(item):
        figDirs.append(item)
#
# make sure all the png images have a place holder eps file
#
flist = []
for item in figDirs:
    dlist = []
    for path, subdirs, files in os.walk(item):
        for fn in files:
            dlist.append(os.path.join(path, fn))
    for fn in dlist:
        if fn[-3:]=="png" and os.path.isfile(fn):
            flist.append(fn[:-3]+"eps")

# Now flist is a list of dummy eps place holder files I need
for fn in flist:
    shutil.copyfile("placeholder.eps", fn)
#
# Made the dummy eps files now need to build html doc
#

# build once to get citations for bibtex
process = subprocess.Popen(
    ['htlatex', 'FOQUS_User_Manual', 'htmlcfg'])
process.wait()
if process.returncode:
    print "some error running htlatex first time"
    sys.exit(process.returncode)

# run bibtex
process = subprocess.Popen(
    ['bibtex', 'FOQUS_User_Manual'])
process.wait()
if process.returncode:
    print "some error running htlatex first time"
    sys.exit(process.returncode)

# run htlatex two more times to get all crossrefrences right
for i in [1,2]:
    process = subprocess.Popen(
        ['htlatex', 'FOQUS_User_Manual', 'htmlcfg'])
    process.wait()
    if process.returncode:
        print "some error running htlatex second time"
        sys.exit(process.returncode)

#
# Now should have the manual good to go for most browsers I will delete
# the extra eps files need a copy on the figs folders with html
#
for fn in flist:
    os.remove(fn)

#
# Now create a zip archive of the manual while copying it to the FOQUS help location
#

zf = zipfile.ZipFile('FOQUS_User_Manual_HTML.zip', 'w')

files = [
    "FOQUS_User_Manual.html",
    "FOQUS_User_Manual.css",
    "FOQUS_User_Manual.xref"]
files.extend([fn for fn in os.listdir(".") if fn[-3:] == "png" and fn[0:17] == "FOQUS_User_Manual"])

# Archive & copy files
for fn_src in files:
    zf.write(fn_src)
    fn_dst = os.path.join("../foqus_lib/help/html", fn_src)
    shutil.copyfile(fn_src, fn_dst)

# A function to add a subdir to the zip archive
def zipdir(subdir, zipf):
    # zipfh is zipfile.ZipFile object
    for root, dirs, file_list in os.walk(subdir):
        for f in file_list:
            zipf.write(os.path.join(root, f))

# archive & copy figs subdirs
for figdir in figDirs:
    zipdir(figdir, zf)
    dst = os.path.join("../foqus_lib/help/html", figdir)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(figdir, dst)

zf.close()
