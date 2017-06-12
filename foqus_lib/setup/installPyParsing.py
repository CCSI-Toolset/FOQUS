# This just installs pyparsing.  It is used
# by FOQUS setup to reduce the number of 
# modules that need to be installed manually.
# and people where having trouble finding the
# right thing to install for pyparsing.
#
# It is here as is a separate file because I
# want to run it as a separate process so I don't
# have to import setuptools in the FOQUS installer
# I'm using distutils

from setuptools.command import easy_install
easy_install.main( ['pyparsing'] )