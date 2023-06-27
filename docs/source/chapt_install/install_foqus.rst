.. _install_foqus:

Install FOQUS
-------------

.. note::
   In previous releases we instructed you to download the FOQUS code and install it in place.  As
   of version 1.5.0, this is no longer required unless you are running on Apple silicon.  The below ``pip install`` method is now the
   preferred method to install FOQUS.

To install FOQUS, open the Anaconda prompt (or appropriate terminal or shell depending on operating
system and choice of Python), and run the following commands::

    conda activate ccsi-foqus
    pip install ccsi-foqus
    foqus --make-shortcut  # Windows only

This will install FOQUS and all the required packages into the ``ccsi-foqus`` conda environment.
The last command there will create a Desktop shortcut for easier, non-terminal, startup of FOQUS
(Windows only, for now).

For Apple silicon
-----------------

Open the Anaconda prompt and run the following commands::

    conda activate ccsi-foqus
    conda install pyqt
    git clone https://github.com/CCSI-Toolset/FOQUS
    cd FOQUS
    pip install -e .