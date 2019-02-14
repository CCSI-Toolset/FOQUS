cd ../..
conda uninstall cycler
pip install cycler --trusted-host pypi.python.org
pip install matplotlib --trusted-host pypi.python.org
pip install python-ntlm3 --trusted-host pypi.python.org
pip install configparser --trusted-host pypi.python.org
python setup.py develop