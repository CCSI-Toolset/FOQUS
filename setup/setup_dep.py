import pip

pip.main(['install', 'pyparsing'])
pip.main(['install', 'py4j'])
pip.main(['install', 'requests'])
pip.main(['install', 'networkx'])
pip.main(['install', 'adodbapi > 2.6.0'])
pip.main(['install', 'redis'])
pip.main(['install', 'pymssql'])
pip.main(['install', 'logstash_formatter'])


#from setuptools import setup

#setup(
#    name='foqus_dummy',
#    packages=[],
#    install_requires=[
#        "pyparsing",
#        "py4j",
#        "requests",
#        "networkx",
#        "adodbapi > 2.6.0"],
#    zip_safe=False
#)
